#!/usr/bin/env python3
#!-*- encoding: utf-8 -*-
import argparse
from enum import Enum
import json 
import logging
import ntpath 
import os 
from pathlib import Path 
import re 
import sys 
from typing import List

FLOW_ITEM_START = re.compile(r"^(?P<index>\d+)\.\s*(?P<level>[\!\?]?)\s*(?P<step>.*)", re.MULTILINE)
TITLE_ITEM_START = re.compile(r"^# \.", re.MULTILINE)

class LevelInfo(Enum):
    Normal = 'normal'
    Optional = 'optional'
    Required = 'required'

    @classmethod
    def from_marker(self, marker: str) -> 'LevelInfo':
        if marker == '!':
            return LevelInfo.Required
        elif marker == '?':
            return LevelInfo.Optional
        else:
            return LevelInfo.Normal

    def to_human_name(self):
        if self == LevelInfo.Normal:
            return "Normalny"
        elif self == LevelInfo.Optional:
            return "Opcjonalny"
        elif self == LevelInfo.Required:
            return "Wymagany"

class ProgressInfo(Enum):
    Waiting = 0
    Active  = 1
    Finished = 2

class ChecklistLoadingError(Exception):
    """
    ChecklistLoadingError
    """

class Step:
    def __init__(self, label: str, description: str | None = None, level: 'LevelInfo' = LevelInfo.Normal):
        self.label = label 
        self.description = description or label 
        self.level = level 
        self.state = ProgressInfo.Waiting

    def __str__(self):
        return f"Step(label={self.label!r}, level={self.level.value})"

    def to_dict(self):
        return {
            'label' : self.label,
            'description' : self.description,
            'level' : self.level.value
        }

    @classmethod
    def from_dict(cls, dct):
        return cls(
            label = dct["label"],
            description= dct['description'],
            level = LevelInfo(dct['level'])
        )

class Checklist:
    def __init__(self, title: str, steps: List['Step'], filename: Path):
        self.title = title
        self.steps: List["Step"] = steps or []
        self.filename = filename
        self.basename = ntpath.basename(filename)
    
    def to_dict(self):
        return { "title" : self.title, "steps" : [ step.to_dict() for step in self.steps ], "filename" : str(self.filename) }

    @classmethod
    def from_dict(cls, dct):
        return cls(title = dct["title"], steps = [ Step.from_dict(s) for s in dct["steps"] ], filename = Path(dct["filename"]))

    @classmethod
    def from_file(cls, filepath: Path | str) -> 'Checklist':
        flow = []
        title = None
        first_line = True 
        file = Path(filepath)
        prev_step: Step = None
        with file.open("r", encoding="utf-8") as fi:
            for index, line in enumerate(fi, 1):
                line = line.strip()
                if not line or line.startswith(';;'):
                    continue
                if first_line:
                    if line.startswith('# '):
                        title = line.lstrip("# ")
                        first_line = False 
                        continue
                    else:
                        title = file.name
                        first_line = False 
                if line.startswith('# '):
                    logging.error(f'Title line should only occur at first line. Found at line {index}.')
                    raise ChecklistLoadingError("Title line found outside line 1") 
                
                m = FLOW_ITEM_START.match(line)
                if m is None:
                    if prev_step != None:
                        prev_step.description += ' ' + line.strip()
                    else:
                        logging.error(f"Badly formed line occur at {file.name}:{index}")
                        raise ChecklistLoadingError("Badly formed line found") 
                else:
                    if prev_step != None:
                        if not prev_step.description:
                            prev_step.description = prev_step.label
                        flow.append(prev_step)
                    dct = m.groupdict()
                    prev_step = Step(label = dct["step"], description="", level=LevelInfo.from_marker(dct['level']))

        if prev_step != None:
            flow.append(prev_step)
        flow[0].state = ProgressInfo.Active
        return cls(title = title, steps = flow, filename = file)

class State:
    def __init__(self, checklist: "Checklist", start: int = 0):
        self.active_checklist = checklist
        self.current_step = start

    def confirm_step(self):
        if self.current_step < len(self.active_checklist.steps):
            self.current_step += 1

    def to_dict(self):
        return {
            "active_checklist": self.active_checklist.to_dict(),
            "current_step" : self.current_step
        }

    @property
    def active_step(self) -> 'Step':
        return self.active_checklist.steps[self.current_step]

    def display_steps(self):
        for index, step in enumerate(self.active_checklist.steps, 1):
            char = ' '
            if index < self.current_step - 1:
                char = '|'
            elif index < self.current_step:
                char = 'v' 
            elif index == self.current_step:
                char = 'o'
            else:
                char = ' '
            padding = ' '*(5 - len(str(index)))
            
            print(f"{index}.{padding}[{char}]   {step.label}")
         
    def save(self):
        cache_file = Path(str(self.active_checklist.filename) + ".out")
        with cache_file.open("w", encoding="utf-8") as cache:
            json.dump(self.to_dict(), cache)

    @classmethod
    def load(cls, filename: Path):
        with filename.open("r", encoding="utf-8") as cache:
            dct = json.load(cache)
            return cls(checklist = Checklist.from_dict(dct["active_checklist"]), start = dct["current_step"])

def start_tui(state: State):
    while True:
        if state.current_step == len(state.active_checklist.steps):
            print(f"Zadanie: >>>  {state.active_checklist.title}  <<< powinno być wykonane!")
            sys.exit(0)
        state.display_steps()
        while True:
            print(f"Czy wykonałeś krok:\n[{state.active_step.level.to_human_name()!s}]\t\t{state.active_step.label}\n")
            inp = input(" T/N => ")
            if inp in 'qQ':
                print("Active step: {}".format(state.current_step))
                state.save()
                sys.exit(0)
            if inp[0] in 'yYtT':
                state.confirm_step()
                break
            else:
                os.system("cls")
        os.system("cls")

def cli():
    parser = argparse.ArgumentParser(description="Checklist App")
    parser.add_argument('filename', type=Path, help="Path to the flow file")
    parser.add_argument("--reset", action="store_true", help="Remove cache file")
    args = vars(parser.parse_args())
    if "filename" not in args:
        logging.error("No path provided in cli")
        print("No path provided")
        sys.exit(0)
    filename = args["filename"]
    state = None
    cache_filename = Path(str(filename) + ".out")
    logging.info("Checking for cache file: {!s}".format(cache_filename))
    
    reset_arg = args["reset"]
    cache_exists = cache_filename.exists()

    if reset_arg:
        cache_filename.unlink()
    
    if cache_exists and not reset_arg:
        state = State.load(cache_filename)
    else:
        try:
            checklist = Checklist.from_file(filename)
            state = State(checklist = checklist, start = 0)
        except ChecklistLoadingError:
            logging.error(f"There was problem with loading checklist: {filename!s}")
            sys.exit(0)

    start_tui(state)
