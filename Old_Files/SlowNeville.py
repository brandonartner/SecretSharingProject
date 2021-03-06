from fractions import Fraction
from Toolkit import find_congruence_with_divisibility

class SlowNeville:
    ''' Incremental implementation of Neville's method
    '''
    
    def __init__(self, k, p):
        # two empty lists to store x and y
        # values respectively
        self.k = k
        self.p = p
        self.values = [[], []]
        
    def addKey(self, key):
        ''' Adds given key and feeds forward 
        '''
        
        # splitting the key across first two lists
        self.values[0].append(key[0])
        self.values[1].append(key[1])
        
        # 
        for idx, lst in enumerate(self.values[1:]):
            # we can create a new polynomial with the two values in the list
            if len(lst) == 2:
                val = self.firstOrderLag(idx)
                
                if idx == len(self.values)-2:
                    self.values.append([find_congruence_with_divisibility(val)])
                else:
                    self.values[idx+2].append(find_congruence_with_divisibility(val))
                    
                # remove value from 
                self.values[idx+1].pop(0)
        
        if len(self.values[0]) == self.k:
            soln = self.values[-1]
            for i in range(len(self.values)):
                self.values[i] = []
            return soln
     
    def firstOrderLag(self, idx):
        j = -1
        i = j - (idx + 1)
        
        x1 = self.values[0][i]
        x2 = self.values[0][j]
            
        y1 = self.values[idx+1][-2]
        y2 = self.values[idx+1][-1]
        
        num = (0-x2)*y1-(0-x1)*y2
        den = x1-x2

        return Fraction(num, den)


