from argparse import ArgumentParser
import json

description = "Reads a JSON file and loads all of the required modules. Each module is given by the 'module' tag in a program definition."
parser = ArgumentParser(description=description)

parser.add_option('-j','--json',required=true,help="JSON configuration file indicating which modules need to be loaded.")

args = parser.parse_args()
fh = open(args.json,'r')
j = json.loads(fh)

 
