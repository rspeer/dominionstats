import rpy2.robjects as robjects

import convert_to_r_fmt
import game
import pymongo
import random

class WinPredictor:
    def __init__(self):
        # this is expensive, it loads the decision tree into r's environment.
        robjects.r('library(randomForest)')
        robjects.r('load("r5_100kn_500t.rt")')  
        # pass

    def predict_all_turns(self, game_val):
        encoded_states = []
        for game_state in game_val.game_state_iterator():
            encoded_state = (
                convert_to_r_fmt.encode_state_r_fmt(game_val, game_state)
            
        # convert the data into this funny column vector format so that we
        # can turn it into a data frame.
        labelled_column_vecs = {}
        for ind, header_val in enumerate(convert_to_r_fmt.make_header()):
            labelled_column_vecs[header_val] = []
            for encoded_state in encoded_states:
                labelled_column_vecs[header_val].append(encoded_state[ind])

        for k in labelled_column_vecs:
            labelled_column_vecs[k] = robjects.FloatVector(
                labelled_column_vecs[k])
        turn_data = robjects.DataFrame(labelled_column_vecs)
        var_name = 'rf_pred_dataframe' + str(random.randint(0, 1000000))
        robjects.globalenv[var_name] = turn_data
        predict_cmd = 'predict(r5, %s)' % var_name
        predictions = list(robjects.r(predict_cmd))
        robjects.r.rm(var_name)
        return predictions

def main():
    c = pymongo.Connection()
    g = game.Game(c.test.games.find_one())
    predictor = WinPredictor()
    print predictor.predict_all_turns(g)


if __name__ == '__main__':
    main()


        
