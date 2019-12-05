
# coding: utf-8


import sys


Likelihood = {}
Transition = {}
trans_prob = {}
emiss_prob = {}
sentences = []
all_pos = []



def train(train_file):
    ftr = open(train_file, 'r')
    previous = "Begin_Sent"
    for line in ftr:
        if line.strip(): #if a line is not empty 

            word,tag = line.strip().split("\t") 

            if previous not in Transition: #create 2-D hashtable for transition
                Transition[previous] = {}
                if tag not in Transition[previous]:
                    Transition[previous][tag] = 1
                else:
                    Transition[previous][tag] += 1
            else:
                if tag not in Transition[previous]:
                    Transition[previous][tag] = 1
                else:
                    Transition[previous][tag] += 1


            if tag not in Likelihood: #create 2-D hashtable for emission 
                Likelihood[tag] = {}
                if word not in Likelihood[tag]:
                    Likelihood[tag][word] = 1
                else:
                    Likelihood[tag][word] += 1
            else:
                if word not in Likelihood[tag]:
                    Likelihood[tag][word] = 1
                else:
                    Likelihood[tag][word] += 1

            previous = tag

        if line in ['\n', '\r\n']: #if a line is empty

            if previous not in Transition:
                Transition[previous] = {}
                if "End_Sent" not in Transition[previous]:
                    Transition[previous]["End_Sent"] = 1
                else:
                    Transition[previous]["End_Sent"] += 1
            else:
                if "End_Sent" not in Transition[previous]:
                    Transition[previous]["End_Sent"] = 1
                else:
                    Transition[previous]["End_Sent"] += 1

            previous = "Begin_Sent"
            
    #calculate the transition probability
    for key, transition_dict in Transition.items():
        total = 0
        for tag, count in transition_dict.items():
            total += count 

        for tag, cnt in transition_dict.items():
            if tag not in trans_prob:
                trans_prob[tag] = {}
                trans_prob[tag][key] = cnt / total
            else:
                trans_prob[tag][key] = cnt / total
                
    #calculate the emission probability
    for tag, emission_dict in Likelihood.items():
        total = 0
        for word, cnt in emission_dict.items():
            total += cnt 

        for word, cnt in emission_dict.items():
            if word not in emiss_prob:
                emiss_prob[word] = {}
                emiss_prob[word][tag] = cnt / total
            else:
                emiss_prob[word][tag] = cnt / total



#To avoid the product exceed the  smallest number 
def product(num1,num2,num3):
    smallest = 4.4e-300
    product = num1*num2*num3
    if product <= smallest:
        return product * 100000
        #return smallest
    else:
        return product



def test(test_file):
    ftr2 = open(test_file, 'r')
    temp = []
    for line in ftr2:
        if line.strip():
            word = line.strip()
            temp.append(word)

        if line in ['\n', '\r\n']:
            sentences.append(temp)
            temp = []
    
    #get possible tags
    possible_tags = []
    possible_tags.append("Begin_Sent")
    for tags in Likelihood.keys():
        possible_tags.append(tags)
    possible_tags.append("End_Sent")
    
    for sent in sentences:
        #create a 2-D array, columns are states, rows are words
        viterbi = []
        for i in range(len(possible_tags) + 1):
            viterbi.append([])
            for j in range(len(sent) + 3):
                viterbi[i].append(None)

        #fill out the states and words in the table, viterbi[0][0] is just a space 
        viterbi[0][0] = "space"
        viterbi[0][1] = 0
        viterbi[1][1] = 1 #Begin_Sent state is definite
        viterbi[0][-1] = len(viterbi[0]) - 2 
        for i in range(2, len(viterbi[0]) - 1):
            viterbi[0][i] = sent[i - 2]
        for j in range(1, len(viterbi)):
            viterbi[j][0] = possible_tags[j - 1]

        #Filling out states in position 1 

        #Handling OOV case 
        if viterbi[0][2] not in emiss_prob.keys():
            for n in range(2, len(viterbi)):
                if viterbi[n][0] == "End_Sent":
                    continue
                elif (viterbi[n][0] in Transition["Begin_Sent"].keys()):
                    viterbi[n][2] = trans_prob[viterbi[n][0]]['Begin_Sent']*(1/1000)
                else:
                    viterbi[n][2] = None
        else:
        #In vocabulary 
            for n in range(2, len(viterbi)):
                if viterbi[n][0] == "End_Sent":
                    continue
                elif viterbi[n][0] in Transition["Begin_Sent"].keys() and viterbi[n][0] in emiss_prob[viterbi[0][2]].keys():
                    viterbi[n][2] = trans_prob[viterbi[n][0]]['Begin_Sent'] * emiss_prob[viterbi[0][2]][viterbi[n][0]]
                else:
                    viterbi[n][2] = None
        
        #keep track of the pos tag we want to keep for the first token
        temp_track = {}
        backpointer = []
        for n in range(2, len(viterbi)):
            if viterbi[n][2] != None:
                temp_track[viterbi[n][0]] = viterbi[n][2]
        sorted_t = sorted(temp_track.items(), key = lambda d : d[1], reverse = True)
        backpointer.append(sorted_t[0][0])
        for k, v in sorted_t:
            temp_track[k] = v

        #Filling out other spaces (except end state) in viterbi and backpointer table 
        for col in range(3, len(viterbi[0])): #loop colomn by colomn
            #when reaching the last column:
            if viterbi[0][col] == len(viterbi[0]) - 2:
                for tag, value in temp_track.items(): #tag = previous tag 
                    if viterbi[len(viterbi)-1][col] == None or value > viterbi[len(viterbi)-1][col]:
                        viterbi[len(viterbi)-1][col] = value

            #rest of the tokens 
            else:
                #Not OOV
                if viterbi[0][col] in emiss_prob.keys(): #viterbi[0][col] = token 
                    #loop row by row, without reaching End_Sent
                    for row in range(2, len(viterbi) - 1):
                        if viterbi[row][0] in emiss_prob[viterbi[0][col]].keys(): #viterbi[row][0] = current tag
                            for tag, val in temp_track.items(): #tag = previous tag
                                #check if P(viterbi[row][0] | tag) exists 
                                if tag in trans_prob[viterbi[row][0]].keys():
                                    #calculate the temp_score, previous score * emiss_prob * trans_prob 
                                    temp_score = val * emiss_prob[viterbi[0][col]][viterbi[row][0]] * trans_prob[viterbi[row][0]][tag]

                                    #store the highest score in the slot 
                                    if viterbi[row][col] == None or temp_score > viterbi[row][col]:
                                        viterbi[row][col] = temp_score
                                
                                else: #error occurs when no matches for any word | POS, pos | previous pos pairs, then all of the columns would be none
                                    viterbi[row][col] = emiss_prob[viterbi[0][col]][viterbi[row][0]] * val * 1/1000


                else:
                #OOV
                    for row in range(2, len(viterbi)-1):
                        for tag, val in temp_track.items():
                            if tag in trans_prob[viterbi[row][0]].keys():
                                #calculate the temp_score, previous score * emiss_prob * trans_prob 
                                temp_score = val * 1/1000 * trans_prob[viterbi[row][0]][tag]

                                #store the highest score in the slot 
                                if viterbi[row][col] == None or temp_score > viterbi[row][col]:
                                    viterbi[row][col] = temp_score
                                    
                            else: #error occurs when no matches for any word | POS, pos | previous pos pairs, then all of the columns would be none
                                    viterbi[row][col] = 1/1000 * val * 1/1000

                #reset the temp_track
                temp_track = {}
                for n in range(2, len(viterbi) - 1):
                    if viterbi[n][col] != None:
                        temp_track[viterbi[n][0]] = viterbi[n][col]
                sorted_t = sorted(temp_track.items(), key = lambda d : d[1], reverse = True)
                backpointer.append(sorted_t[0][0])
                for k, v in sorted_t:
                    temp_track[k] = v
        #append the pos tagger for the current sentence to all_pos
        all_pos.append(backpointer)



if __name__ == '__main__':
    if len(sys.argv) != 3:
        print ("please enter: python qf262_Viterbi_HW3.py WSJ_02-21.pos WSJ_23.words")
        exit()
    train_file = sys.argv[1]
    test_file = sys.argv[2]
    train(train_file)
    test(test_file)
    
    write_to_file = open("submission.pos","w")
    for i in range(len(sentences)):
        for j in range(len(sentences[i])):
            write_to_file.write(sentences[i][j] + "\t" + all_pos[i][j] + "\n")
            
        write_to_file.write("\n")

