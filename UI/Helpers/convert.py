

FINAL_RNK    = { 1:"①", 2:"②", 3:"③", 4:"④", 5:"⑤", 6:"⑥",
                 "F":"(F)", "L":"(L)", "S":"(S)", "K":"(K)"       }

PREFINAL_RNK = { 1:"[ 1 ]", 2:"[ 2 ]", 3:"[ 3 ]", 4:"[ 4 ]", 5:"[ 5 ]", 6:"[ 6 ]",
                 "F":"[F]", "L":"[L]", "S":"[S]", "K":"[K]"       }

def convert_rank(rank:int|str, final:int, prefinal:int):

    if final:
        return FINAL_RNK[rank]
    elif prefinal:
        return PREFINAL_RNK[rank]
    else:
        return rank
