March 31, 2014
Nathaniel Watson

Kwality: A tool for running multiple quality metrics on read, mapping, and
variant inputs


SUMMARY: 
Kwality performs multiple QC analyses for data in FASTQ, BAM, and VCF format. Analyses run in parallel, apart from specified dependencies, on a cluster.
Cluster jobs are executed and monitored by Simple Job Manager (SJM; see
https://github.com/StanfordBioinformatics/SJM/blob/master/doc/MANUAL.txt),
which is aware of job dependencies and keeps track of each job's status. The
input to the Kwality package is a configuration file in JASON format, which
must abide by the JSON schema packaged within the tool. The main program in the
package is clinicalQc.py, which loads the schema and conf file, validates the
conf file against the schema, and builds the SJM file, which can subsequently
be launched with the sjm command.


JSON SCHEMA:
The packaged schema schema.json defines the rules and structure of the
user-generated conf file. The schema allows for

1) Comments - Any key prefixed with a "#" will be ignored.

2) Analyses - Multiple analyses can be defined within the top-level "analyses"
object.  An analysis is defined as an executable that can have command-line (CL) options and
arguments. Dependencies can also be specified. Each analysis object may contain a
"params" object, an "args" object, and a "qsub" object.  The params object
lays out the analysis parameters/options, while the args object contains an array of all the non-option arguments of the analysis, 
whereas the qsub object gives the Grid Engine job arguments and values for running the analysis on the cluster.

2) General Resources - A top-level 'resources' object.  This is where you may 
define common keys that can appear in multiple analyses. A particular key in an analysis can reference a
resource by setting its value to the resource name, prefixed by a "$" symbol;
however, the reference must be at the beginning of the value. For example, if we have the reference 
					"vcf": "sample1.vcf"
then it is possible for all analyses to reference this vcf file.

3) QSUB Resources - A top-level 'qsub' object that contains qsub options to
use across all analyses. This is usefule for setting common options only once,
rather that repetitively for each analysis. A reference is made to a qsub
resource in the same way as to a general resource.


In addition to the general resources specified in the conf file, resources may
also be specified on the CL as arguments in key=value form, where
each argument is spearated by whitespace. These CL resources will be added to
the conf's resources, and replacing any having the same name. 
Read the schema for a full understanding of the structure and semantics of a
conf file.



