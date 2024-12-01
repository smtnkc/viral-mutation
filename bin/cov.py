from mutation import *
import pickle
import csv

np.random.seed(1)
random.seed(1)

def parse_args():
    import argparse
    parser = argparse.ArgumentParser(description='Coronavirus sequence analysis')
    parser.add_argument('model_name', type=str,
                        help='Type of language model (e.g., hmm, lstm)')
    parser.add_argument('--namespace', type=str, default='cov',
                        help='Model namespace')
    parser.add_argument('--dim', type=int, default=512,
                        help='Embedding dimension')
    parser.add_argument('--batch_size', type=int, default=87,
                        help='Training minibatch size')
    parser.add_argument('--inference_batch_size', type=int, default=1000,
                        help='Inference minibatch size')
    parser.add_argument('--n_epochs', type=int, default=1,
                        help='Number of training epochs')
    parser.add_argument('--seed', type=int, default=1,
                        help='Random seed')
    parser.add_argument('--checkpoint', type=str, default=None,
                        help='Model checkpoint')
    parser.add_argument('--train', action='store_true',
                        help='Train model')
    parser.add_argument('--train_split', action='store_true',
                        help='Train model on portion of data')
    parser.add_argument('--test', action='store_true',
                        help='Test model')
    parser.add_argument('--embed', action='store_true',
                        help='Analyze embeddings')
    parser.add_argument('--semantics', action='store_true',
                        help='Analyze mutational semantic change')
    parser.add_argument('--combfit', action='store_true',
                        help='Analyze combinatorial fitness')
    parser.add_argument('--reinfection', action='store_true',
                        help='Analyze reinfection cases')
    parser.add_argument('--newmut', action='store_true',
                        help='Analyze reinfection cases')
    parser.add_argument('--cscs', action='store_true',
                        help='Analyze CSCS')
    parser.add_argument('--use_avg_embedding', action='store_true',
                        help='Use average embedding for semantics while calculating CSCS')
    args = parser.parse_args()
    return args

def parse_viprbrc(entry):
    fields = entry.split('|')
    if fields[7] == 'NA':
        date = None
    else:
        date = fields[7].split('/')[0]
        date = dparse(date.replace('_', '-'))

    country = fields[9]
    from locations import country2continent
    if country in country2continent:
        continent = country2continent[country]
    else:
        country = 'NA'
        continent = 'NA'

    from mammals import species2group

    meta = {
        'strain': fields[5],
        'host': fields[8],
        'group': species2group[fields[8]],
        'country': country,
        'continent': continent,
        'dataset': 'viprbrc',
    }
    return meta

def parse_nih(entry):
    fields = entry.split('|')

    country = fields[3]
    from locations import country2continent
    if country in country2continent:
        continent = country2continent[country]
    else:
        country = 'NA'
        continent = 'NA'

    meta = {
        'strain': 'SARS-CoV-2',
        'host': 'human',
        'group': 'human',
        'country': country,
        'continent': continent,
        'dataset': 'nih',
    }
    return meta

def parse_gisaid(entry):
    fields = entry.split('|')

    type_id = fields[1].split('/')[1]

    if type_id in { 'bat', 'canine', 'cat', 'env', 'mink',
                    'pangolin', 'tiger' }:
        host = type_id
        country = 'NA'
        continent = 'NA'
    else:
        host = 'human'
        from locations import country2continent
        if type_id in country2continent:
            country = type_id
            continent = country2continent[country]
        else:
            country = 'NA'
            continent = 'NA'

    from mammals import species2group

    meta = {
        'strain': fields[1],
        'host': host,
        'group': species2group[host].lower(),
        'country': country,
        'continent': continent,
        'dataset': 'gisaid',
    }
    return meta

def process(fnames, out_file_name):
    seqs = {}
    for fname in fnames:
        for record in SeqIO.parse(fname, 'fasta'):
            if len(record.seq) < 1000:
                continue
            #if str(record.seq).count('X') > 0:
                #continue
            if record.seq not in seqs:
                seqs[record.seq] = []
            if fname == 'data/cov/viprbrc_db.fasta':
                meta = parse_viprbrc(record.description)
            elif fname == 'data/cov/gisaid.fasta':
                meta = parse_gisaid(record.description)
            elif fname == 'data/cov/sars_cov2_seqs.fa':
                meta = parse_nih(record.description)
            else:
                meta = {}
            meta['accession'] = record.description
            seqs[record.seq].append(meta)

    with open(f'data/cov/{out_file_name}', 'w') as of:
        for seq in seqs:
            metas = seqs[seq]
            for meta in metas:
                of.write('>{}\n'.format(meta['accession']))
                of.write('{}\n'.format(str(seq)))

    return seqs

def split_seqs(seqs, split_method='random'):
    train_seqs, test_seqs = {}, {}

    tprint('Splitting seqs...')
    for idx, seq in enumerate(seqs):
        if idx % 10 < 2:
            test_seqs[seq] = seqs[seq]
        else:
            train_seqs[seq] = seqs[seq]
    tprint('{} train seqs, {} test seqs.'
           .format(len(train_seqs), len(test_seqs)))

    return train_seqs, test_seqs

def sample_seqs(seqs):
    sample_seqs = {}

    tprint('Sampling seqs...')
    for idx, seq in enumerate(seqs):
        if idx % 100 == 0:
            sample_seqs[seq] = seqs[seq]

    tprint('{} seqs are sampled.'.format(len(sample_seqs)))

    return sample_seqs

def setup(args):
    ref_fnames = [  'data/cov/wt_before_alignment.fasta',
                'data/cov/omic_before_alignment.fasta'
                # 'data/cov/sars_cov2_seqs.fa',
                # 'data/cov/viprbrc_db.fasta',
                # 'data/cov/gisaid.fasta' 
        ]
    
    mut_fnames = [  'data/cov/eris_before_alignment.fasta',
                'data/cov/new_before_alignment.fasta',
                'data/cov/gpt_before_alignment.fasta'
        ]

    ref_seqs = process(ref_fnames, "ref_seqs.fa")
    mut_seqs = process(mut_fnames, "mut_seqs.fa")

    #mut_seqs = dict(list(mut_seqs.items())[:10])
    ref_max_len = max([ len(seq) for seq in ref_seqs ])
    mut_max_len = max([ len(seq) for seq in mut_seqs ])
    seq_len = max(ref_max_len, mut_max_len) + 2
    vocab_size = len(AAs) + 2

    tprint("SEQ LEN: {}".format(seq_len))
    tprint("VOCAB SIZE: {}".format(vocab_size))
    tprint('{} unique omicron sequences with the max length of {}.'.format(len(ref_seqs), ref_max_len))
    tprint('{} unique mutant sequences with the max length of {}.'.format(len(mut_seqs), mut_max_len))

    tprint("LOADING MODEL...")
    model = get_model(args, seq_len, vocab_size)
    tprint("MODEL LOADED.")

    return model, ref_seqs, mut_seqs

def interpret_clusters(adata):
    clusters = sorted(set(adata.obs['louvain']))
    for cluster in clusters:
        tprint('Cluster {}'.format(cluster))
        adata_cluster = adata[adata.obs['louvain'] == cluster]
        for var in [ 'host', 'country', 'strain' ]:
            tprint('\t{}:'.format(var))
            counts = Counter(adata_cluster.obs[var])
            for val, count in counts.most_common():
                tprint('\t\t{}: {}'.format(val, count))
        tprint('')

def plot_umap(adata, categories, namespace='cov'):
    for category in categories:
        sc.pl.umap(adata, color=category,
                   save='_{}_{}.png'.format(namespace, category))

def analyze_embedding(args, model, seqs, vocabulary):

    seqs = embed_seqs(args, model, seqs, vocabulary, use_cache=True)

    X, obs = [], {}
    obs['n_seq'] = []
    obs['seq'] = []
    for seq in seqs:
        meta = seqs[seq][0]
        X.append(meta['embedding'].mean(0))
        for key in meta:
            if key == 'embedding':
                continue
            if key not in obs:
                obs[key] = []
            obs[key].append(Counter([
                meta[key] for meta in seqs[seq]
            ]).most_common(1)[0][0])
        obs['n_seq'].append(len(seqs[seq]))
        obs['seq'].append(str(seq))
    X = np.array(X)

    adata = AnnData(X)
    for key in obs:
        adata.obs[key] = obs[key]

    sc.pp.neighbors(adata, n_neighbors=20, use_rep='X')
    sc.tl.louvain(adata, resolution=1.)
    sc.tl.umap(adata, min_dist=1.)

    sc.set_figure_params(dpi_save=500)
    plot_umap(adata, [ 'host', 'group', 'continent', 'louvain' ])

    interpret_clusters(adata)

    adata_cov2 = adata[(adata.obs['louvain'] == '0') |
                       (adata.obs['louvain'] == '2')]
    plot_umap(adata_cov2, [ 'host', 'group', 'country' ],
              namespace='cov7')

def make_mutant(wt_seq, mutations):
    indiv_muts, mut_seq = [], wt_seq[:]
    for mutation in mutations:
        aa_orig = mutation[0]
        if 'del' in mutation:
            aa_pos = int(mutation[1:-3]) - 1
            aa_mut = '-'
        elif '|' in mutation and 'ins' in mutation:
            aa_pos = int(mutation.split('|')[0][1:]) - 1
            aa_mut = mutation.split('|')[1][3:]
        else:
            aa_pos = int(mutation[1:-1]) - 1
            aa_mut = mutation[-1]
        assert(mut_seq[aa_pos] == aa_orig)
        mut_seq = mut_seq[:aa_pos] + aa_mut + mut_seq[aa_pos + 1:]
    mut_seq = mut_seq.replace('-', '')
    return mut_seq

def grammaticality_change(word_pos_prob, seq, mutations, args, vocabulary, model,
                          verbose=False,):
    if len(mutations) == 0:
        return 0

    mut_probs = []
    for mutation in mutations:
        if 'del' in mutation or 'ins' in mutation:
            continue
        aa_orig = mutation[0]
        aa_pos = int(mutation[1:-1]) - 1
        aa_mut = mutation[-1]
        if (seq[aa_pos] != aa_orig):
            tprint(mutation)
        assert(seq[aa_pos] == aa_orig)
        mut_probs.append(word_pos_prob[(aa_mut, aa_pos)])

    return np.mean(np.log10(mut_probs))

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

def get_escape_potential(gramm, change, null_gramm, null_change):
    assert(len(null_gramm) == len(null_change))
    count = 0
    for ng, nc in zip(null_gramm, null_change):
        if ng < gramm or nc < change:
            count += 1
    return count / len(null_gramm), count

def analyze_new_mutations(args, model, seqs, vocabulary):
    uk_mutations = [
        'H69del', 'V70del', 'Y145del', 'N501Y', 'A570D',
        'P681H', 'T716I', 'S982A',  'D1118H'
    ]
    sa_mutations = [
        'D80A', 'D215G', 'K417N', 'E484K', 'N501Y', 'A701V'
    ]
    andreano_mutations = [
        'F140del', 'E484K', 'Y248|insKTRNKSTSRRE|L249'
    ]

    names = [ 'B.1.1.7', 'B.1.351', 'PT188-EM' ]
    mutations_list = [ uk_mutations, sa_mutations, andreano_mutations ]

    wt_seq = str(SeqIO.read('data/cov/cov2_spike_wt.fasta', 'fasta').seq)

    seqs = embed_seqs(
        args, model, seqs, vocabulary, use_cache=True, namespace='cov2_null'
    )
    wt_embedding = seqs[wt_seq][0]['embedding']

    y_pred = predict_sequence_prob(
        args, wt_seq, vocabulary, model, verbose=False
    )

    word_pos_prob = {}
    for pos in range(len(wt_seq)):
        for word in vocabulary:
            word_idx = vocabulary[word]
            prob = y_pred[pos + 1, word_idx]
            word_pos_prob[(word, pos)] = prob

    sorted_seqs = sorted([
        seq for seq in seqs
        if ((seqs[seq][0]['strain'] == 'SARS-CoV-2' or
             'hCoV-19' in seqs[seq][0]['strain']) and
            seq != wt_seq and seq.startswith('M') and seq.endswith('HYT'))
    ])

    null_changes = np.array([
        abs(seqs[seq][0]['embedding'].mean(0) - wt_embedding.mean(0)).sum()
        for seq in sorted_seqs
    ])
    null_grammar = np.array([
        grammaticality_change(word_pos_prob, wt_seq, get_mutations(wt_seq, seq),
                              args, vocabulary, model)
        for seq in sorted_seqs
    ])
    tprint('Background set of {} sequences'.format(len(null_changes)))

    mut_changes, mut_gramms = [], []
    for name, mutations in zip(names, mutations_list):

        mut_seq = make_mutant(wt_seq, mutations)
        mut_embedding = embed_seqs(
            args, model, { mut_seq: [ {} ] }, vocabulary, verbose=False,
        )[mut_seq][0]['embedding']
        mut_change = abs(mut_embedding.mean(0) - wt_embedding.mean(0)).sum()
        mut_changes.append(mut_change)

        mut_gramm = grammaticality_change(word_pos_prob, wt_seq, mutations,
                                          args, vocabulary, model)
        mut_gramms.append(mut_gramm)

        tprint('{}: Grammar percentile = {}%'.format(
            name, ss.percentileofscore(null_grammar, mut_gramm)
        ))
        tprint('{}: Change percentile = {}%'.format(
            name, ss.percentileofscore(null_changes, mut_change)
        ))
        tprint('{}: Combined percentile = {}, N = {}'.format(
            name, *get_escape_potential(mut_gramm, mut_change,
                                        null_grammar, null_changes)
        ))

        for idx in np.argwhere(null_changes > mut_change).ravel():
            tprint('\tlen: {},\tstart char: {}'.format(len(sorted_seqs[idx]),
                                                      sorted_seqs[idx][0]))
            if name == 'andreano':
                tprint('\tHigher change mutations:')
                from Bio import pairwise2
                alignment = pairwise2.align.globalms(
                    wt_seq, sorted_seqs[idx], 5, -4, -3, -.1,
                    one_alignment_only=True,
                )[0]
                for idx, (ch1, ch2) in enumerate(zip(alignment[0], alignment[1])):
                    if ch1 != ch2:
                        tprint('\t\t{}{}{}'.format(ch1, idx + 1, ch2))

        for mutation in mutations:
            mut_seq = make_mutant(wt_seq, [ mutation ])
            embedding = embed_seqs(
                args, model, { mut_seq: [ {} ] }, vocabulary, verbose=False,
            )[mut_seq][0]['embedding']
            change = abs(embedding.mean(0) - wt_embedding.mean(0)).sum()

            mut_gramm = grammaticality_change(word_pos_prob, wt_seq, [ mutation ],
                                              args, vocabulary, model)

            tprint('\tMutation {}: change = {}, percentile = {}%'.format(
                mutation, change,
                ss.percentileofscore(null_changes, change)
            ))

    plt.figure(figsize=(4, 8))
    ax = sns.violinplot(data=null_changes, inner=None, color='white')
    ax = sns.stripplot(data=null_changes, color='#aaaaaa')
    ax.scatter([ 0 ] * len(mut_changes), mut_changes, color='#800000')
    for name, change in zip(names, mut_changes):
        ax.annotate(name, (0.01, change))
    ax.get_xaxis().set_visible(False)
    plt.ylabel('Semantic change')
    plt.tight_layout()
    plt.savefig('figures/cov_new_mut.png', dpi=500)
    plt.close()

    plt.figure(figsize=(4, 8))
    plt.scatter(null_grammar, null_changes, color='#aaaaaa')
    plt.scatter(mut_gramms, mut_changes, color='#800000')
    ax = plt.gca()
    for name, gramm, change in zip(names, mut_gramms, mut_changes):
        ax.annotate(name, (gramm + 0.1, change))
    plt.xlabel('Fitness')
    plt.ylabel('Semantic change')
    plt.tight_layout()
    plt.savefig('figures/cov_new_mut_cscs.png', dpi=500)
    plt.close()




























def analyze_cscs(args, model, seqs, mut_seqs, vocabulary):

    tprint("Generating Omicron embeddings...")
    checkpoint_name = args.checkpoint.split('.')[0].split('/')[-1]
    seqs = embed_seqs(args, model, seqs, vocabulary, use_cache=True, namespace=f'null_by_{checkpoint_name}')

    if args.use_avg_embedding:
        # get first omicron sequence as reference sequence
        for record in SeqIO.parse("data/cov/omic_before_alignment.fasta", "fasta"):
            tmp_seq = str(record.seq)
            if len(tmp_seq) == 1273 and tmp_seq.count('X') == 0:
                ref_seq = str(tmp_seq)
                break
        # get average embedding of seqs
        max_length = 1280  # Example length, adjust as needed
        padded_embeddings = [pad_embedding(embedding, max_length) for embedding in [seqs[seq][0]['embedding'] for seq in seqs]]
        avg_embedding = np.mean(padded_embeddings, axis=0)
        ref_embedding = avg_embedding
    else:
        ref_seq = str(SeqIO.read('data/cov/wt_before_alignment.fasta', 'fasta').seq)
        ref_embedding = seqs[ref_seq][0]['embedding']

    tprint("Generating mutant embeddings...")
    mut_embeddings = embed_seqs(args, model, mut_seqs, vocabulary, use_cache=True, namespace=f'mutants_by_{checkpoint_name}')

    tprint("Predicting sequence probabilities for {} mutants...".format(len(mut_seqs)))
    y_pred = predict_sequence_prob(args, ref_seq, vocabulary, model, verbose=False)

    tprint("Generating word position probabilities...")
    word_pos_prob = {}
    for pos in range(len(ref_seq)):
        for word in vocabulary:
            word_idx = vocabulary[word]
            prob = y_pred[pos + 1, word_idx]
            word_pos_prob[(word, pos)] = prob

    tprint("Sorting sequences...")
    sorted_seqs = sorted([
        seq for seq in seqs
        if (seq != ref_seq and seq.startswith('M') and seq.endswith('HYT'))
    ])

    tprint("Generating null changes...")
    null_changes = np.array([
        abs(seqs[seq][0]['embedding'].mean(0) - ref_embedding.mean(0)).sum()
        for seq in sorted_seqs
    ])

    tprint("Generating null grammaticality distributions...")
    null_grammar = np.array([
        grammaticality_change(word_pos_prob, ref_seq, get_mutations(ref_seq, seq),
                              args, vocabulary, model)
        for seq in sorted_seqs
    ])
    tprint('Background set of {} sequences'.format(len(null_changes)))

 
    # Initialize lists to store results
    mut_sc_values, mut_gr_values, mut_cscs_values = [], [], []
    mut_gr_per_values, mut_sc_per_values, mut_cscs_per_values, mut_Ns = [], [], [], []

    mut_seq_ids = []

    # Loop through each mutant sequence
    for mut_seq in mut_seqs:

        # Compute embedding and change
        mut_embedding = mut_embeddings[mut_seq][0]['embedding']
        mut_seq_id = mut_embeddings[mut_seq][0]['accession']
        mut_sc = abs(mut_embedding.mean(0) - ref_embedding.mean(0)).sum()
        mut_sc_values.append(mut_sc)

        # Get mutations
        mutations = get_mutations(ref_seq, mut_seq)

        # Compute grammaticality change
        mut_gr = grammaticality_change(word_pos_prob, ref_seq, mutations, args, vocabulary, model)
        mut_gr_values.append(mut_gr)

        # Calculate escape potential values
        mut_cscs = mut_gr + mut_sc
        mut_cscs_values.append(mut_cscs)
        mut_gr_per = ss.percentileofscore(null_grammar, mut_gr)
        mut_gr_per_values.append(mut_gr_per)
        mut_sc_per = ss.percentileofscore(null_changes, mut_sc)
        mut_sc_per_values.append(mut_sc_per)
        mut_cscs_per, mut_N = get_escape_potential(mut_gr, mut_sc, null_grammar, null_changes)
        mut_cscs_per *= 100
        mut_cscs_per_values.append(mut_cscs_per)
        mut_Ns.append(mut_N)
        mut_seq_ids.append(mut_seq_id)

        tprint("{}: gr = {:.4f} ({:.1f}%), sc = {:.4f} ({:.1f}%), cscs = {:.4f} (> {:.1f}% of null values), N = {}/{}".format(
            mut_seq_id, mut_gr, mut_gr_per, mut_sc, mut_sc_per, mut_cscs, mut_cscs_per, mut_N, len(null_changes)))

    # Save results to CSV
    out_path = f'outs/cscs_scores_avg_{checkpoint_name}.csv' if args.use_avg_embedding else f'outs/cscs_scores_wt_{checkpoint_name}.csv'
    with open(out_path, 'w') as f:
        writer = csv.writer(f)
        writer.writerow(['name', 'gr', 'gr_per', 'sc', 'sc_per', 'cscs', 'cscs_per', 'N'])
        for i in range(len(mut_seqs)):
            writer.writerow([mut_seq_ids[i], mut_gr_values[i], mut_gr_per_values[i], mut_sc_values[i], 
                            mut_sc_per_values[i], mut_cscs_values[i], mut_cscs_per_values[i], mut_Ns[i]])











def pad_embedding(embedding, max_length):
    if embedding.shape[0] < max_length:
        # Pad with zeros if embedding length is less than max_length
        padding = np.zeros((max_length - embedding.shape[0], embedding.shape[1]))
        return np.vstack([embedding, padding])
    elif embedding.shape[0] > max_length:
        # Truncate if embedding length is greater than max_length
        return embedding[:max_length]
    else:
        return embedding



if __name__ == '__main__':
    args = parse_args()

    AAs = [
        'A', 'R', 'N', 'D', 'C', 'Q', 'E', 'G', 'H',
        'I', 'L', 'K', 'M', 'F', 'P', 'S', 'T', 'W',
        'Y', 'V', 'X', 'Z', 'J', 'U', 'B',
    ]
    vocabulary = { aa: idx + 1 for idx, aa in enumerate(sorted(AAs)) }

    model, seqs, mut_seqs = setup(args)
    # seqs = sample_seqs(seqs) # random sampling 1% of the dataset
    tprint("SETUP COMPLETE.")

    if 'esm' in args.model_name:
        args.checkpoint = args.model_name
    elif args.checkpoint is not None:
        model.model_.load_weights(args.checkpoint)
        tprint('Model summary:')
        print(model.model_.summary())

    if args.train:
        batch_train(args, model, seqs, vocabulary, batch_size=args.batch_size)

    if args.train_split or args.test:
        train_test(args, model, seqs, vocabulary, split_seqs)

    if args.embed:
        if args.checkpoint is None and not args.train:
            raise ValueError('Model must be trained or loaded '
                             'from checkpoint.')
        no_embed = { 'hmm' }
        if args.model_name in no_embed:
            raise ValueError('Embeddings not available for models: {}'
                             .format(', '.join(no_embed)))
        analyze_embedding(args, model, seqs, vocabulary)

    if args.semantics:
        if args.checkpoint is None and not args.train:
            raise ValueError('Model must be trained or loaded '
                             'from checkpoint.')

        from escape import load_baum2020, load_greaney2020
        tprint('Baum et al. 2020...')
        seq_to_mutate, seqs_escape = load_baum2020()
        analyze_semantics(args, model, vocabulary,
                          seq_to_mutate, seqs_escape, comb_batch=5000,
                          prob_cutoff=0, beta=1., plot_acquisition=True,)
        tprint('Greaney et al. 2020...')
        seq_to_mutate, seqs_escape = load_greaney2020()
        analyze_semantics(args, model, vocabulary,
                          seq_to_mutate, seqs_escape, comb_batch=5000,
                          min_pos=318, max_pos=540, # Restrict to RBD.
                          prob_cutoff=0, beta=1., plot_acquisition=True,
                          plot_namespace='cov2rbd')

    if args.combfit:
        if args.checkpoint is None and not args.train:
            raise ValueError('Model must be trained or loaded '
                             'from checkpoint.')

        from combinatorial_fitness import load_starr2020
        tprint('Starr et al. 2020...')
        wt_seqs, seqs_fitness = load_starr2020()
        strains = sorted(wt_seqs.keys())
        for strain in strains:
            analyze_comb_fitness(args, model, vocabulary,
                                 strain, wt_seqs[strain], seqs_fitness,
                                 comb_batch=10000, prob_cutoff=0., beta=1.)

    if args.reinfection:
        if args.checkpoint is None and not args.train:
            raise ValueError('Model must be trained or loaded '
                             'from checkpoint.')

        from reinfection import load_to2020, load_ratg13, load_sarscov1
        from plot_reinfection import plot_reinfection

        tprint('To et al. 2020...')
        wt_seq, mutants = load_to2020()
        analyze_reinfection(args, model, seqs, vocabulary, wt_seq, mutants,
                            namespace='to2020')
        plot_reinfection(namespace='to2020')
        null_combinatorial_fitness(args, model, seqs, vocabulary,
                                   wt_seq, mutants, n_permutations=100000000,
                                   namespace='to2020')

        tprint('Positive controls...')
        wt_seq, mutants = load_ratg13()
        analyze_reinfection(args, model, seqs, vocabulary, wt_seq, mutants,
                            namespace='ratg13')
        plot_reinfection(namespace='ratg13')
        wt_seq, mutants = load_sarscov1()
        analyze_reinfection(args, model, seqs, vocabulary, wt_seq, mutants,
                            namespace='sarscov1')
        plot_reinfection(namespace='sarscov1')

    if args.newmut:
        if args.checkpoint is None and not args.train:
            raise ValueError('Model must be trained or loaded '
                             'from checkpoint.')

        analyze_new_mutations(args, model, seqs, vocabulary)

    if args.cscs:
        tprint("Analyzing CSCS...")
        if args.checkpoint is None and not args.train:
            raise ValueError('Model must be trained or loaded '
                             'from checkpoint.')

        analyze_cscs(args, model, seqs, mut_seqs, vocabulary)
