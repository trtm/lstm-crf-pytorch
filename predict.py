import sys
from utils import *

def load_model():
    word_to_idx = load_word_to_idx(sys.argv[2])
    tag_to_idx = load_tag_to_idx(sys.argv[3])
    idx_to_tag = [tag for tag, _ in sorted(tag_to_idx.items(), key = lambda x: x[1])]
    model = rnn_crf(len(word_to_idx), len(tag_to_idx))
    print(model)
    model.eval()
    load_checkpoint(sys.argv[1], model)
    return model, word_to_idx, tag_to_idx, idx_to_tag

def run_model(model, idx_to_tag, data):
    z = len(data)
    while len(data) < BATCH_SIZE:
        data.append([-1, "", [EOS_IDX], []])
    data.sort(key = lambda x: -len(x[2]))
    batch_len = len(data[0][2])
    batch = [x[2] + [PAD_IDX] * (batch_len - len(x[2])) for x in data]
    result = model.decode(LongTensor(batch))
    for i in range(z):
        data[i].append(tuple(idx_to_tag[j] for j in result[i]))
    return [(x[1], x[3], x[4]) for x in sorted(data[:z])]

def predict(lb = False):
    idx = 0
    data = []
    result = []
    model, word_to_idx, tag_to_idx, idx_to_tag = load_model()
    fo = open(sys.argv[4])
    for line in fo:
        line = line.strip()
        if lb:
            x, y = zip(*[re.split("/(?=[^/]+$)", x) for x in line.split()])
            x = [normalize(x) for x in x]
        else:
            x, y = tokenize(line, UNIT), ()
        x = [word_to_idx[i] if i in word_to_idx else UNK_IDX for i in x]
        data.append([idx, line, x, y])
        if len(data) == BATCH_SIZE:
            result.extend(run_model(model, idx_to_tag, data))
            data = []
        idx += 1
    fo.close()
    if len(data):
        result.extend(run_model(model, idx_to_tag, data))
    return result

if __name__ == "__main__":
    if len(sys.argv) != 5:
        sys.exit("Usage: %s model word_to_idx tag_to_idx test_data" % sys.argv[0])
    print("cuda: %s" % CUDA)
    with torch.no_grad():
        result = predict()
        for x, y0, y1 in result:
            print((x, y0, y1))
            # print(iob_to_txt(x, y1, UNIT))
