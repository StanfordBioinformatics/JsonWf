
import json
import sjm
from argparse import ArgumentParser

description = ""
parser = ArgumentParser(description=description)
parser.add_argument('-c','--conf-file',required=True,help="Configuration file in JSON format.")
parser.add_argument('-b','--bam-file',help="Mappings file in BAM format")
parser.add_argument('--vcf-file',help="Varicant Call File in VCF format")
parser.add_argument('-r','--reference',required=True,required=True
parser.add_argument('--out-dir',help="Output folder")
parser.add_argument('-v','--verbose',help="Print extra details to stdout.")

args = parser.parse_args()

