# read 4 fasta files and check if any sequence is duplicated

from Bio import SeqIO

# read fasta files
seqs = []
for file in ["data/cov/omic_before_alignment.fasta",
             #"data/cov/new_before_alignment.fasta",
             #"data/cov/eris_before_alignment.fasta",
             "data/cov/gpt_before_alignment.fasta"
             ]:
    with open(file, "r") as f:
        for record in SeqIO.parse(f, "fasta"):
            seqs.append(str(record.seq))

# count duplicates
duplicates = 0

for i in range(len(seqs)):
    for j in range(i+1, len(seqs)):
        if seqs[i] == seqs[j]:
            duplicates += 1
            print(seqs[i], "\n")

print(f"Number of duplicates: {duplicates}")