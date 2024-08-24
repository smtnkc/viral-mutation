
from Bio import SeqIO


def get_mutations(seq1, seq2):
    # Perform global sequence alignment between two sequences.
    # 5: match score, -4: mismatch penalty, -3: gap opening penalty, -0.1: gap extension penalty.
    # `one_alignment_only=True` ensures that only the best alignment is returned.

    mutations = []
    from Bio import pairwise2
    alignment = pairwise2.align.globalms(
        seq1, seq2, 5, -4, -3, -.1, one_alignment_only=True,
    )[0]
    pos = 0
    for ch1, ch2 in zip(alignment[0], alignment[1]):
        if ch1 != ch2 and ch1 != '-' and ch2 != '-':
            mutations.append('{}{}{}'.format(ch1, pos + 1, ch2))
        if ch1 != '-':
            pos += 1
    return mutations



for record in SeqIO.parse("data/cov/omic_before_alignment.fasta", "fasta"):
    tmp_seq = str(record.seq)
    if len(tmp_seq) == 1273 and tmp_seq.count('X') == 0:
        omic_seq = str(tmp_seq)
        break
wt_seq = str(SeqIO.read('data/cov/wt_before_alignment.fasta', 'fasta').seq)


mutations = get_mutations(wt_seq, omic_seq)

print('Mutations:', mutations)