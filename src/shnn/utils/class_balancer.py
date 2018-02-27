import numpy as np

id = 0
positive, negative, neutral = 0,0,0
sentence = []
with open('../labeled_data_selected.tsv', 'r') as infile:
    for row in infile:
        _, label, label_numeric, drug, food, sent = row.strip().split('\t')
        # choose unique sentences and down-sample the neutrals
        if sent not in sentence and len(sent) >= 100 and len(sent) <= 200:
            if label == 'positive':
                positive += 1
                sentence.append([str(id), label, label_numeric, drug, food, sent])
                id += 1
            elif label == 'negative':
                negative += 1
                sentence.append([id, label, label_numeric, drug, food, sent])
                id += 1
            else:
                if np.random.uniform() <= 0.333:
                    neutral += 1
                    sentence.append([id, label, label_numeric, drug, food, sent])
                    id += 1

with open('../labeled_data_selected.tsv', 'w') as outfile:
    for sent in sentence:
        id, label, label_numeric, drug, food, s = sent
        outfile.write('{0}\t{1}\t{2}\t{3}\t{4}\t{5}\n'.format(id,label, label_numeric, drug, food, s))
print([positive, negative, neutral])