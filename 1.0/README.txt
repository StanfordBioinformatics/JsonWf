
-bash-4.1$ pwd
/srv/gsfs0/projects/gbsc/Clinical_Service/cases/case0001/hugeseq-1.2
-bash-4.1$ samtools view -h chr20.bam > /srv/gs1/software/gbsc/clinical_qc/TEST/chr20.sam 


/srv/gsfs0/projects/gbsc/Clinical_Service/cases/case0001/hugeseq-1.2
-bash-4.1$ cp chr20.vcf /srv/gs1/software/gbsc/clinical_qc/TEST/
The file size is 28M.


-bash-4.1$ head -n80000 chr20.sam > chr20_80K.sam
-bash-4.1$ rm chr20.sam 
-bash-4.1$ samtools view -Shb chr20_80K.sam > chr20_80K.bam
