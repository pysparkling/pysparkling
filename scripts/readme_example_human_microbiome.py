from pysparkling import Context

by_subject_rdd = Context().textFile(
    's3n://human-microbiome-project/DEMO/HM16STR/46333/by_subject/*'
)
print(by_subject_rdd.takeSample(True, 1))
