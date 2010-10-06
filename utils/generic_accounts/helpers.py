#-*- coding: utf-8 -*-
#PYTHON
import random


def gen_random_code():
    randint = str(random.randint(100*100, 1000*1000*1000))
    charlist = 'a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,r,s,t,u,v,x,z,k,y,w'.split(',')
    
    random.shuffle(charlist)
    
    i = 0
    code = ''
    for c in charlist:
        try:
            code += c + randint[i]
            i += 1
        except IndexError:
            break

            
    return code

   
if __name__ == '__main__':
      print gen_random_code()