import os
import sys
import re
import types
import copy
    
class SExpParser:
    
    class CommandCell:
        def __init__(self):
            self.op = ''
            self.arglist = []        

    def __init__(self):
        self.FUNC_MAPS = {}
        self.defaultFmObj = ''
        self.parseList = []
        self.execStack = []
        self.sexp = ''

    def parsingSexp(self, sexp, cha='()'):
        self.sexp = sexp
        stack, i, length = [[]], 0, len(sexp)
        atom_end = set('() ')
        while i < length:
            c = sexp[i]
    
            #print c, stack
            reading = type(stack[-1])
            if reading == list:
                if   c == '(': stack.append([])
                elif c == ')': 
                    stack[-2].append(stack.pop())
                    if stack[-1][0] == ('quote',): stack[-2].append(stack.pop())
                #elif c == '"' or c=="'": stack.append('')
                #elif c == "'": stack.append([('quote',)])
                #elif c in whitespace: pass
                else: stack.append((c,))
            elif reading == str:
                #if   c == '"' or c=="'": 
                #    stack[-2].append(stack.pop())
                    #if stack[-1][0] == ('quote',): stack[-2].append(stack.pop())
                if c == '\\': 
                    i += 1
                    stack[-1] += sexp[i]
                else: stack[-1] += c
            elif reading == tuple:
                if c in atom_end:
                    atom = stack.pop()
                    #if atom[0][0].isdigit(): stack[-1].append(eval(atom[0]))
                    #else: stack[-1].append(atom)
                    stack[-1].append(atom)
                    #if stack[-1][0] == ('quote',): stack[-2].append(stack.pop())
                    continue
                else: stack[-1] = ((stack[-1][0] + c),)
            i += 1
            
        result = stack.pop()
        if len(result)!=1:
            raise Exception("wrong passing result!")
        parseResult = result[0]
        self.postProcess(parseResult)
        #self.simplyList(parseResult)
        self.removeSpaces(parseResult)
        self.parseList = parseResult
        return parseResult
    
    def postProcess(self, parseResult):
        for i,m in enumerate(parseResult):
            if type(m)==tuple:
                parseResult[i] = m[0]
            else:
                self.postProcess(m)
        return parseResult
    def removeSpaces(self, parseResult):
        for i, m in enumerate(parseResult):
            if type(m)==list:
                self.removeSpaces(m)
            if i==0:
                if self.isCmd(m)[0]:
                    index = 1
                    while type(parseResult[index])==str and re.match('\s*$', parseResult[index]): index += 1
                    if type(parseResult[index])==str:
                        parseResult[index] = parseResult[index].lstrip()
                    else:
                        del parseResult[1:index]
    def isCmd(self, cmd):
        cmdStr = ''
        processFmObj = None
        
        if type(cmd)==list:
            pass
        else:
            cmd = cmd.strip()
            for funcMap, fmObj in self.FUNC_MAPS.items():
                if cmd in funcMap.getCmdList():
                    cmdStr = cmd
                    processFmObj = fmObj
        return cmdStr, processFmObj
    

    def getSexpOutput(self):
        return self.parseList
        
    def addFuncMap(self, funcMap, isDefault = False):
        self.FUNC_MAPS[funcMap] = funcMap.getFuncMap()
        
        if isDefault:
            self.defaultFmObj = funcMap
            
    def evalCell(self, parseList=[]):
        if len(parseList)==0:
            parseList = self.parseList
            self.execStack.append(parseList)
        for i, v in enumerate(parseList):
            if (type(v) == list):
                self.evalCell(v)
        
        self.simplyList(parseList)
                
        cmdStr, processFmObj = self.isCmd(parseList[0])
        
        
        if cmdStr:
            processFmObj[cmdStr](parseList)
        else:
            self.defaultFmObj.defaultProcess(parseList) 
    def simplyList(self, args):
        index = 0
        while index < len(args):
            m = args[index]
            if type(m)==list:
                if len(m) == 0:
                    del args[index]
                elif len(m) == 1:
                    args[index] = m[0]
                    self.simplyList(m[0])
                    index += 1
                else:
                    self.simplyList(m)
                    index += 1
            else:
                index += 1
class BasicFuncMap ():
    
    def __init__(self, isDebug):
        self.commandList = ["#pdr", "#PDR"     , "#pfr", "#PFR"     , "#pd", "#PD"     , "#c", "#cs", "#cc", "#D"     , "#d", "#sh", "#ps", "#PS"     , "#pf", "#PF"     , "#pm", "#s", "#g", "#m", "#e"]
        self.functionList= ["PDR" , "PDRHidden", "PFR" , "PFRHidden", "PD" , "PDHidden", "C" , "CS" , "CC" , "DHidden", "D" , "SH" , "PS" , "PSHidden", "PF" , "PFHidden", "PM" , "S" , "G" , "M" , "E" ]
        self.substituteDict = {'__[':'(', ']__':')','&nbsp':' ','&nbsn':''}
        self.varSign        = '@'
        self.variableDict = {}
        self.funcMap   = {}
        self.parseList = []
        self.isDebug = isDebug
        
        self.init()
    def init(self):
        cmdList = self.getCmdList()
        ptrList = self.getFuncPtr()        
        for i,v in enumerate(cmdList): self.funcMap[v] = ptrList[i]
        
    def getCmdList(self):
        return self.commandList
    def getFuncPtr(self):
        ptrs = [eval("self."+m) for m in self.functionList]
        return ptrs
    def getFuncMap(self):
        return self.funcMap
    
    def substituteSpecialChars(self, args):
        
        if type(args)==types.StringType:
            result = args
            for k in self.substituteDict.keys():
                result = result.replace(k, self.substituteDict[k])
        else:
            result = copy.deepcopy(args)
            for argIndex in range(0, len(result)):
                if type(result[argIndex]) == types.StringType:
                    for k in self.substituteDict.keys():
                        arg = result[argIndex]
                        result[argIndex] = arg.replace(k, self.substituteDict[k])
                elif type(result[argIndex]) == types.ListType:
                    for n in range(0, len(result[argIndex])):
                        for k in self.substituteDict.keys():
                            str = result[argIndex][n]
                            result[argIndex][n] = str.replace(k, self.substituteDict[k])
        return result
    def substituteVariable(self, args):
        for i, v in enumerate(args):
            #if type(v) == types.ListType and len(v) == 1:
            #    v = v[0]
                #args[i] = v
                
            if type(v) == types.StringType:
                m = re.finditer(self.varSign+'[\w\d]*', v)
                startEnd = []
                variables = []
                for gm in m:
                    startEnd.append(gm.span())
                    variables.append(v[gm.start():gm.end()])
                if startEnd!=[]:
                    del args[i]
                    for index, se in enumerate(startEnd):
                        values = self.variableDict[variables[index]]
                        '''
                                    start = se[0] - 1
                                    while start >=0 and v[start]==' ': start = start - 1                        
            
                                    if type(values)==types.StringType:                            
                                        values = ' '*(se[0]-start-1) + values
                                    else:
                                        self.listSpace[id(values)] = [se[0]-start-1,0]
                                    '''                    
                        if index == 0:
                            prefix = v[:se[0]]
                        else:
                            prefix = v[startEnd[index-1][1]:se[0]]
                        args.insert(i+index*2, prefix)
                        args.insert(i+index*2+1, values)
                    postfix = v[startEnd[-1][1]:]
                    args.insert(i+len(startEnd)*2, postfix)
        index = 0        
        while index<len(args):
            if type(args[index])==str and args[index]=='':
                del args[index]
            else:
                index += 1
    def defaultProcess(self, args):
        self.concatArgs(args)
    def E(self, args):
        if self.isDebug:
            self.printArgs("E", args)
        self.substituteVariable(args)
        commands = self.getOneArgs(args)
        commands = self.substituteSpecialChars(commands)
        
        
        result = []
        for arg in commands:
            out = eval(arg)
            result.append(str(out).splitlines())
            
        self.writeToParseList(args, result)
    def G(self, args):
        if self.isDebug:
            self.printArgs("G", args)
        self.substituteVariable(args)
        minList, maxList = self.getTwoArgs(args)
        
        strToList = lambda s: [int(s)] if type(s) == types.StringType else [int(e) for e in s]
        
        minList = strToList(minList)    
        maxList = strToList(maxList)
        stepList = [1]*len(minList)
        if len(args) == 4:
            stepList = strToList(args[3])
            
        resultList = []
        for m in range(0, len(minList) ):
            resultList = resultList + range(minList[m], maxList[m], stepList[m])
        
        
        resultList = [str(m) for m in resultList]
        self.writeToParseList(args, resultList)
        return
    def M(self, args):
        if self.isDebug:
            self.printArgs("M", args)
        
        self.substituteVariable(args)
        
        for i, arg in enumerate(args):
            args[i] = self.substituteSpecialChars(arg)
        
        listIndex = []
        for index in range(0, len(args)):
            arg = args[index]
            if type(arg)==types.ListType:
                listIndex.append(index)
                
        numOfList = len(listIndex)
        if numOfList >1:
            cantactedList = []
            oldList = [[i] for i in args[listIndex[0]]]

            for i in range(1, numOfList):
                secondList = args[listIndex[i]]
                
                num = len(oldList)
                
                
                for m in range(0, num):
                    for n in range(0, len(secondList)):
                        cantactedList.append(copy.deepcopy(oldList[m]) )
                        cantactedList[-1].append(secondList[n])
                oldList = copy.deepcopy(cantactedList)
                result = [] 
                for m in range(0, len(cantactedList)):
                    outStr = ""
                    strIndex = 0
                    for i in range(1, len(args) ):
                        if i not in listIndex:
                            outStr = outStr + args[i]
                        else:
                            outStr = outStr + cantactedList[m][strIndex]
                            strIndex = strIndex+1
                    
                    result.append(outStr)                
        else:
            result = self.concatArgs(args, False, 'concat', 1)

        self.writeToParseList(args, result)
    
    def PSWork(self, args):
        
        self.substituteVariable(args)
        text, pt = self.getTwoArgs(args)
        text = self.substituteSpecialChars(text)
    
        prefix = ''
        if type(pt)==list:
            pt = pt[0]
        pt = pt.strip()
        pt = self.substituteSpecialChars(pt)
        numOfGroup = re.compile(pt).groups
        for g in range(0, numOfGroup+1):
            self.variableDict[self.varSign+prefix+str(g)] = []
    
        parseResult = []
        for t in text:
            searchResult = re.search(pt, t)
            if searchResult!=None:
                parseResult.append(searchResult.group(0))
                for g in range(0, numOfGroup+1):
                    self.variableDict[self.varSign+prefix+str(g)].append(searchResult.group(g))
    
        return parseResult        
    def PSHidden(self, args):
        if self.isDebug:
            self.printArgs("PSHidden", args)
        self.PSWork(args)
        del args[:]
    def PS(self, args):
        if self.isDebug:
            self.printArgs("PS", args)        
        parseResult = self.PSWork(args)
        self.writeToParseList(args, parseResult)
    def PM(self, args):
        if self.isDebug:
            self.printArgs("PM", args)
        self.substituteVariable(args)
        text, pt = self.getTwoArgs(args)
        text = self.substituteSpecialChars(text)
        
        result =[]


        if type(text)==str:
            if type(pt) == str:
                pass
            elif type(pt) == list and len(pt)==1:
                pt = pt[0]
            else:
                raise Exception("wrong parameters for PF")
            pt = pt.strip()
            pt = self.substituteSpecialChars(pt)
            if re.match(pt, text)!=None:
                result.append(text)
        else:
            if type(pt) == str:
                pt = pt.strip()
                pt = self.substituteSpecialChars(pt)
                for t in text:
                    if re.match(pt, t):
                        result.append(t)
            else:
                if len(pt) != len(folder):
                    raise Exception("The size of pt must be equal to the size of folers.")
                for i, f in enumerate(folder):
                    p = self.substituteSpecialChars(pt[i])
                    for t in text:
                        if re.match(p, t):
                            result.append(t) 
                
        self.writeToParseList(args, result)
        
        return 
    def PFWork(self, args):
        self.substituteVariable(args)
        folder, pt = self.getTwoArgs(args, '.')
        folder = self.substituteSpecialChars(folder)
    
        self.variableDict[self.varSign+'f']=[]        
    
        if type(folder)==str:
            files = os.listdir(folder)
            if type(pt) == str:
                pass
            elif type(pt) == list and len(pt)==1:
                pt = pt[0]
            else:
                raise Exception("wrong parameters for PF")
            pt = pt.strip()
            pt = self.substituteSpecialChars(pt)
    
            result = [f for f in files if os.path.isfile(os.path.join(folder, f)) and re.match(pt, f)]
            self.variableDict[self.varSign+'f']=[folder]*len(result)
        else:
            result = []
            if type(pt) == str:
                pt = pt.strip()
                pt = self.substituteSpecialChars(pt)
                for f in folder:
                    for m in os.listdir(f):
                        if os.path.isfile(os.path.join(f, m)) and re.match(pt, m):
                            self.variableDict[self.varSign+'f'].append(f)
                            result.append(m)
            else:
                if len(pt) != len(folder):
                    raise Exception("The size of pt must be equal to the size of folers.")
                for i, f in enumerate(folder):
                    p = self.substituteSpecialChars(pt[i])
                    for m in os.listdir(f):
                        if os.path.isfile(os.path.join(f, m)) and re.match(p, m):
                            self.variableDict[self.varSign+'f'].append(f)
                            result.append(m)
    
        baseNamePt = '^(.+)\.(.*)$'       
        self.variableDict[self.varSign+'b']=[]
        self.variableDict[self.varSign+'e']=[]
        self.variableDict[self.varSign+'n']=result
        for f in result:
            searchResult = re.search(baseNamePt, f)
            self.variableDict[self.varSign+'b'].append(searchResult.group(1))
            self.variableDict[self.varSign+'e'].append(searchResult.group(2))
        return result        
    def PFHidden(self, args):
        if self.isDebug:
            self.printArgs("PFHidden", args)
        self.PFWork(args)
        del args[:]
        
    def PF(self, args):
        if self.isDebug:
            self.printArgs("PF", args)        
        result = self.PFWork(args)
        self.writeToParseList(args, result)
    def PDWork(self, args):
        self.substituteVariable(args)
        folder, pt = self.getTwoArgs(args, '.')
        folder = self.substituteSpecialChars(folder)
    
        self.variableDict[self.varSign+'f']=[]        
    
        if type(folder)==str:
            files = os.listdir(folder)
            if type(pt) == str:
                pass
            elif type(pt) == list and len(pt)==1:
                pt = pt[0]
            else:
                raise Exception("wrong parameters for PF")
            pt = pt.strip()
            pt = self.substituteSpecialChars(pt)
    
            result = [f for f in files if os.path.isdir(os.path.join(folder, f)) and re.match(pt, f)]
            self.variableDict[self.varSign+'f']=[folder]*len(result)
        else:
            result = []
            if type(pt) == str:
                pt = pt.strip()
                pt = self.substituteSpecialChars(pt)
                for f in folder:
                    for m in os.listdir(f):
                        if os.path.isdir(os.path.join(f, m)) and re.match(pt, m):
                            self.variableDict[self.varSign+'f'].append(f)
                            result.append(m)
            else:
                if len(pt) != len(folder):
                    raise Exception("The size of pt must be equal to the size of folers.")
                for i, f in enumerate(folder):
                    p = self.substituteSpecialChars(pt[i])
                    for m in os.listdir(f):
                        if os.path.isdir(os.path.join(f, m)) and re.match(p, m):
                            self.variableDict[self.varSign+'f'].append(f)
                            result.append(m)
        return result
    def PD(self, args):
        if self.isDebug:
            self.printArgs("PD", args)        
        result = self.PDWork(args)
        self.writeToParseList(args, result)   
    def PDHidden(self, args):
        if self.isDebug:
            self.printArgs("PDHidden", args)
        self.PDWork(args)
        del args[:]        
    def PFRWork(self, args):
        self.substituteVariable(args)
        folder, pt = self.getTwoArgs(args, '.')
        folder = self.substituteSpecialChars(folder)
    
        self.variableDict[self.varSign+'f']=[] 
        result = []
        if type(folder)==str:
            if type(pt) == str:
                pass
            elif type(pt) == list and len(pt)==1:
                pt = pt[0]
            else:
                raise Exception("wrong parameters for PF")
            pt = pt.strip()
            pt = self.substituteSpecialChars(pt)
            
            for fpathe,dirs,fs in os.walk(folder):
                for f in fs:
                    if re.match(pt, f):
                        result.append(f)
                        self.variableDict[self.varSign+'f'].append(fpathe)
        else:
            if type(pt) == str:
                pt = pt.strip()
                pt = self.substituteSpecialChars(pt)
                for f in folder:
                    for fpathe,dirs,fs in os.walk(f):
                        for fe in fs:
                            if re.match(pt, fe):
                                self.variableDict[self.varSign+'f'].append(fpathe)
                                result.append(fe)
            else:
                if len(pt) != len(folder):
                    raise Exception("The size of pt must be equal to the size of folers.")
                for i, f in enumerate(folder):
                    p = self.substituteSpecialChars(pt[i])
                    for fpathe,dirs,fs in os.walk(f):
                        for fe in fs:
                            if re.match(p, fe):
                                self.variableDict[self.varSign+'f'].append(fpathe)
                                result.append(fe)
        baseNamePt = '^(.+)\.(.*)$'       
        self.variableDict[self.varSign+'b']=[]
        self.variableDict[self.varSign+'e']=[]
        self.variableDict[self.varSign+'n']=result
        for f in result:
            searchResult = re.search(baseNamePt, f)
            self.variableDict[self.varSign+'b'].append(searchResult.group(1))
            self.variableDict[self.varSign+'e'].append(searchResult.group(2))
        return result           
    def PFR(self, args):
        if self.isDebug:
            self.printArgs("PFR", args)        
        result = self.PFRWork(args)
        self.writeToParseList(args, result)   
    def PFRHidden(self, args):
        if self.isDebug:
            self.printArgs("PFRHidden", args)        
        result = self.PFRWork(args)
        del args[:]
    def PDRWork(self, args):
        self.substituteVariable(args)
        folder, pt = self.getTwoArgs(args, '.')
        folder = self.substituteSpecialChars(folder)
    
        self.variableDict[self.varSign+'f']=[] 
        result = []
        if type(folder)==str:
            if type(pt) == str:
                pass
            elif type(pt) == list and len(pt)==1:
                pt = pt[0]
            else:
                raise Exception("wrong parameters for PF")
            pt = pt.strip()
            pt = self.substituteSpecialChars(pt)
            
            for fpathe,dirs,fs in os.walk(folder):
                for dr in dirs:
                    if re.match(pt, dr):
                        result.append(dr)
                        self.variableDict[self.varSign+'f'].append(fpathe)
        else:
            if type(pt) == str:
                pt = pt.strip()
                pt = self.substituteSpecialChars(pt)
                for f in folder:
                    for fpathe,dirs,fs in os.walk(f):
                        for dr in dirs:
                            if re.match(pt, dr):
                                self.variableDict[self.varSign+'f'].append(fpathe)
                                result.append(dr)
            else:
                if len(pt) != len(folder):
                    raise Exception("The size of pt must be equal to the size of folers.")
                for i, f in enumerate(folder):
                    p = self.substituteSpecialChars(pt[i])
                    for fpathe,dirs,fs in os.walk(f):
                        for dr in dirs:
                            if re.match(p, dr):
                                self.variableDict[self.varSign+'f'].append(fpathe)
                                result.append(dr)
        return result
    def PDR(self, args):
        if self.isDebug:
            self.printArgs("PDR", args)        
        result = self.PDRWork(args)
        self.writeToParseList(args, result)   
    def PDRHidden(self, args):
        if self.isDebug:
            self.printArgs("PDRHidden", args)        
        result = self.PDRWork(args)
        del args[:]
    def S(self, args):
        if self.isDebug:
            self.printArgs("S", args)
        self.substituteVariable(args)
        commands = self.getOneArgs(args)
        commands = self.substituteSpecialChars(commands)
        if type(commands)==str:
            commands=[commands]
            
        result = []
        
        for arg in commands:
            out = os.popen(arg).read()
            for line in out.splitlines():
                result.append(line)
        self.writeToParseList(args, result)
    def SH(self, args):
        if self.isDebug:
            self.printArgs("SH", args)

        self.substituteVariable(args)
        commands = self.getOneArgs(args)
        commands = self.substituteSpecialChars(commands)
        if type(commands)==str:
            commands=[commands]
            
        self.writeToParseList(args, commands)
    def DWork(self, args):
        self.substituteVariable(args)
        text, pre = self.getTwoArgs(args,'','')
        
        pre = pre.strip()
        varName = self.varSign+pre
        self.variableDict[varName] = text
        
        if pre[0]=='z' and type(text) == list:
            for i,t in enumerate(text):
                self.variableDict[varName+str(i+1)] = t
    
        return text
    def D(self, args):
        if self.isDebug:
            self.printArgs("D", args)        
        text = self.DWork(args)
        self.writeToParseList(args, text)
    def DHidden(self, args):
        if self.isDebug:
            self.printArgs("DHidden", args)
        self.DWork(args)
        del args[:]
    def C(self, args):
        if self.isDebug:
            self.printArgs("C", args)
        text = self.getOneArgs(args, '')
        if type(text)==list:
            result = "".join(text)
        else:
            result = text
        self.writeToParseList(args, result)
    def CS(self, args):
        if self.isDebug:
            self.printArgs("CS", args)
        text = self.getOneArgs(args)
        if type(text)==list:
            result = " ".join(text)
        else:
            result = text
        self.writeToParseList(args, result)        
    def CC(self, args):
        if self.isDebug:
            self.printArgs("CS", args)
        text, char = self.getTwoArgs(args)
        char = char.strip()
        if type(text)==list:
            result = char.join(text)
        else:
            result = text
        self.writeToParseList(args, result)        
    
    def writeToParseList(self, args, result):
        del args[:]
        if type(result)==list:
            for m in result: args.append(m)        
        else:
            args.append(result)
    def concatArgs(self, args, isInplace = True, dp = 'nop', *be):
        #['a',['1','2'],'b'] - >
        #['a<cha>1<cha>b','a<cha>2<cha>b']
        #['a','b'] -> ['a<cha>b']
        listLength = -1
        if len(be)==0:     begin,end = 0    ,len(args)
        elif len(be) == 1: begin,end = be[0],len(args)
        elif len(be) == 2: begin,end = be[0],be[1]
            
        for ai in range(begin, end):
            arg = args[ai]
            if type(arg) ==  types.ListType:
                if listLength==-1:
                    listLength = len(arg)
                elif len(arg)!=1 and len(arg)!=listLength:
                    raise Exception("The list in args should have equal length!")
        if listLength == -1:
            if dp == 'concat':
                string = ''.join(args[begin:end])
                if isInplace:
                    del args[begin:end]
                    args.insert(begin, string)
                    return
                else:
                    return string
            elif dp=='nop':
                if not isInplace:
                    return args[begin:end]
                else:
                    return
        result = []
        for m in range(0, listLength):
            concatStr = ''
            for n in range(begin, end):
                arg = args[n]
                if type(arg) == types.StringType:
                    concatStr = concatStr + arg
                elif type(arg) == types.ListType:
                    concatStr = concatStr + arg[m]
            result.append(concatStr)
        if isInplace:
            del args[begin:end]
            args.insert(begin, result)
            return
        else:
            return result
    

                    
    def getOneArgs(self, args, d1=''):
        numOfArgs = len(args)
        for v in args:
            if type(v)==str and re.match('^\s*$', v):
                numOfArgs -= 1    
        if numOfArgs == 1:
            return d1
        elif numOfArgs >= 2:
            d1tmp = self.concatArgs(args, False, 'concat', 1, len(args))
            if type(d1tmp)==list:
                return [s for s in d1tmp]
            else:
                return d1tmp
        
    def getTwoArgs(self, args, d1='', d2=''):
        numOfArgs = len(args)
        for v in args:
            if type(v)==str and re.match('^\s*$', v):
                numOfArgs -= 1
        if numOfArgs == 1:
            return d1, d2
        elif numOfArgs == 2:
            return d1, args[-1]
        elif numOfArgs == 3:
            d1 = args[1]
            d2 = args[-1]
            return d1, d2
        else:
            d2 = args[-1]
            d1tmp = self.concatArgs(args, False, 'concat', 1, len(args)-1)
            if type(d1tmp)==str:
                d1 = d1tmp
            else:
                d1 = [s for s in d1tmp]
            return d1, d2
    def getThreeArgs(self, args, d1='', d2='', d3=''):
        pass
    def printArgs(self, str,args):
        print "---Eval "+str+" with args:---"
        for arg in args:
            print arg
        print "-----------------------"        
def constructArgv(args, command, sexpList):
    sexpIndexList = []
    specialString = '__!@!@%03d!@!@__'
    
    for sexpIndex in range(0, len(sexpList)):
        command = command.replace(sexpList[sexpIndex], specialString%sexpIndex)
    argv = command.split()
    
    sexpIndex = 0
    for i in range(0, len(argv)):
        while specialString%sexpIndex in argv[i]:
            sexpIndexList.append(i)
            argv[i] = argv[i].replace(specialString%sexpIndex, sexpList[sexpIndex])
            sexpIndex = sexpIndex + 1
    return sexpIndexList, argv

def execCommand(commandList, isOnlyShow, isParallelWork):
    if isOnlyShow:
        for c in commandList:
            print c
        return
    if isParallelWork:
        for c in commandList:
            out = os.popen(arg).read()
            print out
    else:
        for c in commandList:
            os.system(c)
def main():
    isOnlyShow = False
    isParallelWork = False
    isDebug = False
    optionIndex = 1

    while True:
        option = sys.argv[optionIndex]
        if   option == '-s':
            isOnlyShow = True
            indexAdd = 1
        elif option == '-p':
            isParallelWork = True
            indexAdd = 1
        elif option == '-d':
            isDebug = True
            indexAdd = 1
        else:
            break
        
        optionIndex += indexAdd
    
    if isDebug:
        for i in range(0,len(sys.argv)):
            print sys.argv[i]    
    parser = SExpParser()
    parser.addFuncMap(BasicFuncMap(isDebug), True)
    
    
    command =  " ".join(sys.argv[optionIndex:])
    command = "(#sh "+command+")"
    
    result = parser.parsingSexp(command)
    parser.evalCell()
    commandList = parser.getSexpOutput()
    execCommand(commandList, isOnlyShow, isParallelWork)

main()