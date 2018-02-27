import re

id = 0
sentences = []
with open('../labeled_data.tsv','r') as infile:
    for row in infile:
        _, label, label_numeric, drug, food, sentence = row.strip().split('\t')
        FOOD_DRUG_RE =  re.compile(r'^(?=.*\b{drug}\b)(?=.*\b{food}\b).*$'.format(drug=drug.lower(), food=food.lower()))
        if re.search(FOOD_DRUG_RE, sentence.lower()):
            sentences.append([id, label, label_numeric, drug, food, sentence])
            id += 1
with open('../labeled_data_selected.tsv', 'w') as outfile:
    for sentence in sentences:
        id, label, label_numeric, drug, food, sent = sentence
        outfile.write('{0}\t{1}\t{2}\t{3}\t{4}\t{5}\n'.format(id,label, label_numeric, drug, food, sent))

