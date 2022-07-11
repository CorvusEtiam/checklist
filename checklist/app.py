import logging
from checklist import cli 

if __name__ == "__main__":
    logging.basicConfig(filename="debug.log", format="[%(levelname)s] %(message)s -- %(asctime)s")
    cli()