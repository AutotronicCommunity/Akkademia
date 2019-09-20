import time
from data import *
from build_data import preprocess

TEST_DATA_SIZE_FOR_LAMBDAS = 3


def hmm_train(sents):
    """
        sents: list of tagged sentences
        Returns: the q-counts and e-counts of the sentences' tags, total number of tokens in the sentences
    """

    print("Start training")
    total_tokens = 0
    q_tri_counts, q_bi_counts, q_uni_counts, e_word_tag_counts, e_tag_counts = {}, {}, {}, {}, {}
    ### YOUR CODE HERE

    # e_tag_counts
    for sentence in sents:
        for token in sentence:
            key = token[1]
            increment_count(e_tag_counts, key)

    # e_word_tag_counts
    for sentence in sents:
        for token in sentence:
            key = token
            increment_count(e_word_tag_counts, key)

    # New update to enhance performance.
    global most_common_tag
    most_common_tag = {}
    for word, tag in e_word_tag_counts:
        if word not in most_common_tag:
            most_common_tag[word] = (tag, e_word_tag_counts[word, tag])
        elif e_word_tag_counts[word, tag] > most_common_tag[word][1]:
                most_common_tag[word] = (tag, e_word_tag_counts[word, tag])

    # Add *, * to beginning of every sentence and STOP to every end.
    adjusted_sents = []
    for sentence in sents:
        adjusted_sentence = []
        adjusted_sentence.append(('<s>', '<s>'))
        adjusted_sentence.append(('<s>', '<s>'))
        for token in sentence:
            adjusted_sentence.append(token)
        adjusted_sentence.append(('</s>', '</s>'))
        adjusted_sents.append(adjusted_sentence)

    # total_tokens
    for sentence in adjusted_sents:
        total_tokens += (len(sentence) - 2)

    # q_uni_counts
    for sentence in adjusted_sents:
        for token in sentence:
            key = token[1]
            increment_count(q_uni_counts, key)

    # q_bi_counts
    for sentence in adjusted_sents:
        for i in range(1, len(sentence)):
            key = (sentence[i-1][1], sentence[i][1])
            increment_count(q_bi_counts, key)

    # q_tri_counts
    for sentence in adjusted_sents:
        for i in range(2, len(sentence)):
            key = (sentence[i-2][1], sentence[i-1][1], sentence[i][1])
            increment_count(q_tri_counts, key)

    # possible tags
    global possible_tags
    possible_tags = {}
    for sentence in sents:
        for token in sentence:
            if token[0] in possible_tags:
                possible_tags[token[0]].add(token[1])
            else:
                possible_tags[token[0]] = {token[1]}
            #possible_tags[token[0]].add("DEFAULT") #TODO: delete?

    ### END YOUR CODE
    return total_tokens, q_tri_counts, q_bi_counts, q_uni_counts, e_word_tag_counts, e_tag_counts


def hmm_compute_q_e_S(test_data, total_tokens, q_tri_counts, q_bi_counts, q_uni_counts, e_word_tag_counts, e_tag_counts):
    # q
    global q
    q = {}
    for key in q_tri_counts:
        q[key] = (float(q_tri_counts[key])/q_bi_counts[(key[0], key[1])],
                 float(q_bi_counts[(key[1], key[2])])/q_uni_counts[key[1]],
                 float(q_uni_counts[key[2]])/total_tokens)

    # e
    global e
    e = {}
    for key in e_word_tag_counts:
        e[key] = float(e_word_tag_counts[key]) / e_tag_counts[key[1]]

    # n: longest sentence
    n = -1
    for sentence in test_data:
        n_tmp = len(sentence)
        if n_tmp > n:
            n = n_tmp

    # S
    global S
    S = q_uni_counts.keys()


def hmm_viterbi(sent, total_tokens, q_tri_counts, q_bi_counts, q_uni_counts, e_word_tag_counts,e_tag_counts, lambda1, lambda2):
    """
        Receives: a sentence to tag and the parameters learned by hmm
        Returns: predicted tags for the sentence
    """
    predicted_tags = [""] * (len(sent))
    ### YOUR CODE HERE

    # n: sent length
    n = len(sent)
    #print(n)

    # pi + bp
    pi = {}
    bp = {}
    pi[(0, '<s>', '<s>')] = 1

    # Viterbi algorithm
    for k in range(1, n+1):
        try:
            S_u = possible_tags[sent[k-2][0]]
        except:
            S_u = S
        if k == 1:
            S_u = ['<s>']
        for u in S_u:
            try:
                S_v = possible_tags[sent[k-1][0]]
            except:
                S_v = S
            for v in S_v:
                try:
                    e_calc = e[(sent[k-1][0], v)]
                except:
                    continue
                pi_tmp = -1
                bp_tmp = "DEFAULT"
                try:
                    S_w = possible_tags[sent[k-3][0]]
                except:
                    S_w = S
                if k == 1 or k == 2:
                    S_w = ['<s>']
                for w in S_w:
                    try:
                        pi_calc = pi[(k - 1, w, u)]
                    except:
                        continue
                    try:
                        q_calc = lambda1*q[(w, u, v)][0] + lambda2*q[(w, u, v)][1] + (1-lambda1-lambda2)*q[(w, u, v)][2]
                    except:
                        if (u, v) in q_bi_counts:
                            q2 = float(q_bi_counts[(u, v)]) / q_uni_counts[u]
                        else:
                            q2 = 0
                        if v in q_uni_counts:
                            q1 = float(q_uni_counts[v]) / total_tokens
                        else:
                            continue
                        q_calc = lambda2 * q2 + (1 - lambda1 - lambda2) * q1
                    if pi_calc * q_calc * e_calc > pi_tmp:
                        pi_tmp = pi_calc * q_calc * e_calc
                        bp_tmp = w
                if bp_tmp != "DEFAULT":
                    pi[(k, u, v)] = pi_tmp
                    bp[(k, u, v)] = bp_tmp
                else:
                    pi[(k, u, v)] = -1
                    try:
                        bp[(k, u, v)] = most_common_tag[sent[k - 3][0]][0]
                    except:
                        bp[(k, u, v)] = "DEFAULT"

    pi_tmp = -1
    try:
        S_u = possible_tags[sent[n-2][0]]
    except:
        S_u = S
    if n == 1:
        S_u = ['<s>']
    for u in S_u:
        try:
            S_v = possible_tags[sent[n-1][0]]
        except:
            S_v = S
        for v in S_v:
            try:
                pi_calc = pi[(n, u, v)]
            except:
                continue
            try:
                q_calc = lambda1*q[(u, v, '</s>')][0] + lambda2*q[(u, v, '</s>')][1] + \
                         (1-lambda1-lambda2)*q[(u, v, '</s>')][2]
            except:
                if (v, '</s>') in q_bi_counts:
                    q2 = float(q_bi_counts[(v, '</s>')]) / q_uni_counts[v]
                else:
                    q2 = 0
                if '</s>' in q_uni_counts:
                    q1 = float(q_uni_counts['</s>']) / total_tokens
                else:
                    continue
                q_calc = lambda2 * q2 + (1 - lambda1 - lambda2) * q1
            if pi_calc * q_calc > pi_tmp:
                pi_tmp = pi_calc * q_calc
                predicted_tags[n-2] = u
                predicted_tags[n-1] = v

    # If we enter here both predicted_tags[n-1] and predicted_tags[n-2] have not been assigned.
    if predicted_tags[n-1] == "":
        predicted_tags[n - 1] = most_common_tag[sent[n - 1][0]][0]
        predicted_tags[n - 2] = most_common_tag[sent[n - 2][0]][0]

    for k in range(n-2, 0, -1):
        try:
            predicted_tags[k - 1] = bp[(k+2, predicted_tags[k], predicted_tags[k+1])]
        except:
            try:
                predicted_tags[k - 1] = most_common_tag[sent[k - 1][0]][0]
            except:
                predicted_tags[k - 1] = "NNP"

    ### END YOUR CODE
    return predicted_tags


def hmm_compute_accuracy(test_data, lambda1, lambda2):
    correct = 0
    seps = 0
    total = 0
    for sentence in test_data:
        predicted_tags = hmm_viterbi(sentence, 0, {}, {}, {}, {}, {}, lambda1, lambda2)
        for i in range(len(sentence)):
            total += 1
            if sentence[i][1] == predicted_tags[i]:
                correct += 1
            else:
                if len(sentence[i]) > 0 and sentence[i][-1] == "-" or \
                        len(predicted_tags[i]) > 0 and predicted_tags[i][-1] == "-":
                    seps += 1
                #print(sentence[i][1], predicted_tags[i])

    #print("precentage of seps errors: " + str(float(seps) / correct))
    return float(correct) / total


def hmm_choose_best_lamdas(test_data):
    best_lambda1 = -1
    best_lambda2 = -1
    best_accuracy = -1
    for i in range(0, 11, 1):
        for j in range(0, 10 - i, 1):
            lambda1 = i / 10.0
            lambda2 = j / 10.0
            accuracy = hmm_compute_accuracy(test_data, lambda1, lambda2)
            print("For lambda1 = " + str(lambda1), ", lambda2 = " + str(lambda2), \
                ", lambda3 = " + str(1 - lambda1 - lambda2) + " got accuracy = " + str(accuracy))
            if accuracy > best_accuracy:
                best_lambda1 = lambda1
                best_lambda2 = lambda2
                best_accuracy = accuracy
    print("The setting that maximizes the accuracy on the test data is lambda1 = " + \
          str(best_lambda1), ", lambda2 = " + str(best_lambda2), \
        ", lambda3 = " + str(1 - best_lambda1 - best_lambda2) + " (accuracy = " + str(best_accuracy) + ")")

    return best_lambda1, best_lambda2


def hmm_eval(test_data, total_tokens, q_tri_counts, q_bi_counts, q_uni_counts, e_word_tag_counts,e_tag_counts):
    """
    Receives: test data set and the parameters learned by hmm
    Returns an evaluation of the accuracy of hmm
    """
    print("Start evaluation")
    acc_viterbi = 0.0
    ### YOUR CODE HERE

    hmm_compute_q_e_S(test_data, total_tokens, q_tri_counts, q_bi_counts, q_uni_counts, e_word_tag_counts, e_tag_counts)
    lambda1, lambda2 = hmm_choose_best_lamdas(test_data[:TEST_DATA_SIZE_FOR_LAMBDAS])
    #acc_viterbi = hmm_compute_accuracy(test_data, lambda1, lambda2)

    ### END YOUR CODE

    return acc_viterbi, lambda1, lambda2


def run_hmm(train_texts, dev_texts):
    vocab = compute_vocab_count(train_texts)

    total_tokens, q_tri_counts, q_bi_counts, q_uni_counts, e_word_tag_counts, e_tag_counts = hmm_train(train_texts)
    acc_viterbi, lambda1, lambda2 = hmm_eval(dev_texts, total_tokens, q_tri_counts, q_bi_counts, q_uni_counts, e_word_tag_counts, e_tag_counts)
    print("HMM DEV accuracy: " + str(acc_viterbi))

    return lambda1, lambda2


def main():
    start_time = time.time()

    train_texts, dev_texts, sign_to_id, tran_to_id, id_to_sign, id_to_tran = preprocess()
    run_hmm(train_texts, dev_texts)

    train_dev_end_time = time.time()
    print("Train and dev evaluation elapsed: " + str(train_dev_end_time - start_time) + " seconds")

    '''
    if os.path.exists("Penn_Treebank/test.gold.conll"):
        test_sents = read_conll_pos_file("Penn_Treebank/test.gold.conll")
        test_sents = preprocess_sent(vocab, test_sents)
        acc_viterbi = hmm_eval(test_sents, total_tokens, q_tri_counts, q_bi_counts, q_uni_counts,
                                           e_word_tag_counts, e_tag_counts)
        print "HMM TEST accuracy: " + str(acc_viterbi)
        full_flow_end_time = time.time()
        print "Full flow elapsed: " + str(full_flow_end_time - start_time) + " seconds"
    '''


if __name__ == "__main__":
    main()