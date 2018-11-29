# -*- coding: utf-8 -*- 运行python
import os,sys,stat,time
from pyautocad import *
import pywinauto
import pymysql,pymssql
import sysinfo
method=1#0为处理绑定失败的文件，1为普通
restartACS='restartACS.bat'
restartCAD='restartCAD.bat'
cpath='D:\\ACADbindhelper'#sys.path[0]
arx_path=os.path.join(cpath,'iWCapolPurgeIn.arx')
lsp_path='D:\\\\ACADbindhelper\\\\bindfix-origin.lsp'
apps={'CAD':'C:\\Program Files\\Autodesk\\AutoCAD 2012 - Simplified Chinese\\acad.exe','ACS':'D:\\AcsModule\\Client\\AcsTools.exe'}
exceptions=[
    ('',"AutoCAD Application","联机检查解决方案并关闭该程序",'关闭程序'),
    (apps['ACS'],"提示","存在无法绑定的外参，手动绑定完成后.*","bind"),
    (apps['ACS'],"提示","应用程序发生了灾难性故障.*","restart"),
    (apps['ACS'],"异常","File service error.*","restart"),
    (apps['ACS'],"错误","调用CAD返回了错误信息.*","restart"),
    (apps['ACS'],"警告","未找到已打开的AutoCAD程序.*","restart"),
    (apps['ACS'],"异常","函数[PlotFrameSet]发生了错误.*",'取消'),
    (apps['ACS'],"提示","文件.*在ScanXref方法中出错",'确定'),
    (apps['CAD'],"图形另存为","取消",'取消'),
    (apps['CAD'],"加载/卸载自定义设置","关闭",'关闭'),
    (apps['CAD'],"AutoCAD 错误报告","软件问题导致.*",'restart'),
    (apps['CAD'],"注释比例.*","此图形包含大量的注释比例.*",'是'),
    ]

def main():
    (dlg,operation)=Find_Exceptions(exceptions)
    if dlg:
        dlg.print_control_identifiers()
    print(operation)

def print_func(func):#装饰器，打印func名
    def inner(*args,**kwargs):
        print(func.__name__+':')
        print(args,kwargs)
        return func(*args,**kwargs)
    return inner

def autorun(mode=0):
    StartCAD()
    StartACS(method=method)
    while 1:
        time.sleep(1)
        print(time.strftime('%Y-%m-%d %H:%M:%S',time.localtime()))
        (dlg,operation)=Find_Exceptions(exceptions)
        if operation:
            if operation=='bind':
                res=RunBind()
                if res.result!='failed_0':
                    dlg["确定"].click()
                else:
                    log_result(res.name,res.path,res.result)
                    print("try again:")
                    res=RunBind()#再试一下
                    if res.result!='failed_0':
                        dlg["确定"].click()
                    else:
                        dlg["取消"].click()
                        print("取消")
                log_result(res.name,res.path,res.result)
            elif operation=='restart':
                StartCAD()
                StartACS(method)
            else:
                dlg[operation].click()
        CheckMEM()
        clean=BindCleaner().clean()
      
def RunBind():
    bind=Binding()
    bind.get_doc()
    print(bind.name)
    bind.close_other()
    bind.xref_purge()
    bind.bind_xref_1()
    if bind.has_xref():
        bind.remove_unload_xref()
        bind.bind_xref_2()
    else:
        bind.result='success_1'
        return bind
    if bind.has_xref():
        bind.bind_xref_3()
    else:
        bind.result='success_2'
        return bind
    if bind.has_xref():
        bind.result='failed_0'
        return bind
    else:
        bind.result='success_3'
        return bind

def StartACS(method=0):
    while 1:
        print(restartACS)
        os.system(restartACS)
        time.sleep(10)
        dlg=Check_ACS()
        if dlg:
            break
    if method==1:
        dlg['开始绑定'].click()
    else:
        dlg['绑定失败跳过'].click()
        dlg['优先处理绑定失败的文件'].click()
        dlg['开始绑定'].click()

def Check_ACS():
    app=pywinauto.application.Application()
    app.connect(path="D:\\AcsModule\\Client\\AcsTools.exe")
    dlg=app.window(title_re='工具管理器')
    try:
        dlg['开始绑定'].print_control_identifiers()
        return dlg
    except pywinauto.findbestmatch.MatchError:
        return 0

def StartCAD(): 
    while 1:
        print(restartCAD)
        os.system(restartCAD)
        t=30
        while t>0:
            time.sleep(1)
            print("waiting for ACAD: "+str(t))
            t=t-1
        t=1
        while t<90:
            try:
                acad =Autocad(create_if_not_exists=False)
                print(arx_path)
                acad.Application.LoadARX(arx_path)
                return 1
            except:
                time.sleep(2)
                t+=1

def CheckMEM():
    if sysinfo.getSysInfo()['memFree']<600:
        try:
            bind=Binding()
            bind.get_doc()
            bind.close_other()
        except:
            pass

def Find_Exceptions(exceptions):
    for (app_path,title,content_re,operation) in exceptions:
        app=pywinauto.application.Application()
        try:
            try:
                if app_path:
                    app.connect(path=app_path)
                else:
                    app.connect(title_re=title) 
                dlg=app.window(title_re=title)
                crash = dlg.window(title_re=content_re)
                crash.print_control_identifiers()
                return (dlg,operation)
            except (pywinauto.findbestmatch.MatchError,pywinauto.findwindows.ElementNotFoundError):
                pass
            except pywinauto.findwindows.ElementAmbiguousError:
                return (1,'restart')
        except pywinauto.application.ProcessNotFoundError:
            return (1,'restart')
    return (0,0)

'''
class dialog():
    def __init__(self):
        self.app=pywinauto.application.Application()
        self.dlg=0

    def find(self):
        self.app.connect(path="D:\\AcsModule\\Client\\AcsTools.exe")
        try:
            self.dlg =self.app[r"提示"]
            self.dlg[r"存在无法绑定的外参，手动绑定完成后点[确定],放弃绑定点[取消]！"].print_control_identifiers()
        except (pywinauto.findbestmatch.MatchError):
            self.dlg=0
        return self.dlg

    def find_acs_exceptions(self,exceptions):
        self.app.connect(path="D:\\AcsModule\\Client\\AcsTools.exe")
        for (title,content_re,operation) in exceptions:
            self.dlg =self.app.window(title_re=title)
            crash=self.dlg.window(title_re=content_re)
            try:
                crash.print_control_identifiers()
                return operation
            except (pywinauto.findbestmatch.MatchError,pywinauto.findwindows.ElementNotFoundError):
                pass
        return 0
'''
class Binding():
    def __init__(self):
        self.acad =Autocad(create_if_not_exists=False)
        self.acad.Application.LoadARX(arx_path)
        self.result='failed_0'

    def get_doc(self):
        self.doc=self.acad.doc
        self.path,self.name=self.doc.Path,self.doc.Name
        return self.doc

    def has_xref(self):
        self.get_all_xref()
        if self.a_xref_name:
            return True
        else:
            return False

    def get_all_xref(self):#获取所有外参
        lst=[]
        self.a_xref_name=[]
        self.a_xref_path=[]
        self.a_xref_name_path=[]
        self.Blocks=self.doc.Blocks
        for i in range(self.Blocks.Count):
            obj=self.Blocks.item(i)
            if obj.IsXRef:
                lst.append(obj) 
                xname,xpath=obj.Name,obj.Path
                self.a_xref_name.append(xname)
                self.a_xref_path.append(xpath)
                self.a_xref_name_path.append((xname,xpath))
        return lst

    @print_func
    def get_lv1_xref(self):#获取一级外参
        lst=[]
        self.lv1_xref_name=[]
        self.lv1_xref_path=[]
        self.lv1_xref_name_path=[]
        self.get_all_xref()
        self.ModelSpace=self.doc.ModelSpace
        for i in range(self.ModelSpace.Count):
            obj=self.ModelSpace.item(i)
            if obj.ObjectName=="AcDbBlockReference":
                if obj.Name in self.a_xref_name:
                    lst.append(obj)
                    xname,xpath=obj.Name,obj.Path
                    self.lv1_xref_name.append(xname)
                    self.lv1_xref_path.append(xpath)
                    self.lv1_xref_name_path.append((xname,xpath))
        return lst

    def load(self):
        self.doc.SendCommand('(load "%s") ' % lsp_path)

    def audit(self):
        self.doc.SendCommand('(command "audit" "y") ')

    @print_func
    def close_other(self):
        self.get_doc()
        lst=[]
        docs=Autocad(create_if_not_exists=True).app.documents
        for i in range(docs.count):
            if docs[i].Name != self.name and docs[i].Name[0:7] !='Drawing':
                lst.append(docs[i].Name)
        for doc in lst:
            docs[doc].close()

    @print_func
    def xref_purge(self):
        self.load()
        self.get_all_xref()
        if self.a_xref_path:
            for path in self.a_xref_path:
                if path and path!="D:\\AcsModule\\Client\\EmptyDwg.dwg": 
                    fpath=FindFile(path,self.path)
                    if fpath:
                        if os.path.getsize(fpath)>1000000:
                            print("purge file: " +fpath)
                            fpath=SetWrite(fpath)
                            self.purgefile(fpath)
    
    @print_func
    def purgefile(self,fpath):
        self.doc.SendCommand('(purgefile "'+fpath+'") ')

    def count0_lst(self):#获取未参照
        lst=[]
        objs=self.doc.Blocks
        for i in range(objs.Count):
            if objs.item(i).IsXRef:
                if objs.item(i).Count==0:
                    lst.append(objs.item(i))
        return lst

    @print_func
    def remove_count0(self):#拆离未参照
        lst=self.count0_lst()
        if lst:    
            for item in lst:
                self.doc.SendCommand('(command "-xref" "d" "'+item.Name+'") ')
            self.doc.SendCommand('(command "-xref" "r" "*") ')
            lst=self.count0_lst()
            return lst
        else:
            return False


    @print_func
    def remove_unload_xref(self):
        for i in range(5):
            if not self.remove_count0():
                return True
        return False
        
    @print_func
    def bind_xref_1(self):#快速绑定
        self.load()
        self.audit()
        self.doc.SendCommand('(bind-fix) ')
        self.get_all_xref()

    @print_func
    def bind_xref_2(self):#逐个绑定
        self.load()
        self.audit()
        self.get_lv1_xref()
        if self.lv1_xref_name:
            self.doc.SendCommand('(command "-xref" "r" "*") ')
            for name in self.lv1_xref_name:
                self.doc.SendCommand('(command "-xref" "b" "'+name+'") ')
            self.get_all_xref()

    @print_func
    def bind_xref_3(self):#一级深度绑定
        self.load()
        self.audit()
        self.get_lv1_xref()
        if self.has_xref():
            for path in self.lv1_xref_path:
                fpath=FindFile(path,self.path)
                fpath=SetWrite(fpath)
                if fpath:
                    doc2=OpenFile(fpath)
                    if doc2:
                        print(doc2)
                        doc2.bind_xref_1()
                        if doc2.has_xref():
                            doc2.bind_xref_2()
                        if doc2.has_xref():
                            print("Can not bind xref: "+doc2.doc.Name)
                            doc2.doc.close(False)
                        else:
                            doc2.doc.close(True)
            self.doc.SendCommand('(command "-xref" "r" "*") ')       
            self.bind_xref_1()
            if self.has_xref():
                self.bind_xref_2()

class BindCleaner():
    
    def __init__(self):
        self.lst=[]
        self.sorted_list=[]
        self.not_binded=self.GetNotBinded()
        self.f_path=r'C:\Users\virtual\AppData\Local\Temp\AcsTempFile\提资接收区'
    

    def clean(self,keep=10):
        self.GetFolders()
        self.sorted_list=self.BubbleSort(self.lst)
        for (ctime,f,nd) in self.lst[keep:]:
            if (f,) not in self.not_binded:
                print(f)
                os.system('rmdir /s/q "%s"' % nd)

    def BubbleSort(self,blist):
        count = len(blist)
        for i in range(0, count):
            for j in range(i + 1, count):
                if blist[i][0] > blist[j][0]:
                    blist[i], blist[j] = blist[j], blist[i]
        return blist

    def GetNotBinded(self):
        with pymssql.connect(host='10.1.246.1', user="readonly", password="capol!@#456",database="CAPOL_Project") as conn:
            cur=conn.cursor()
            cur.execute(u"SELECT ID FROM ProductFile where RecordState='A' and IsCurrent is null and BindState<>'Binded'")
            return set(cur.fetchall())

    def GetFolders(self):
        f_path=self.f_path
        if os.path.isdir(f_path):
            print(f_path)
        else:
            return 0
        dirs=os.listdir(f_path)
        self.lst=[]
        for f in dirs:
            nd=os.path.join(f_path,f)
            if os.path.isdir(nd):
                ctime=os.stat(nd).st_ctime
                self.lst.append((ctime,f,nd))
        return self.lst

def FindFile(path,find_path):
    if path and find_path:
        (fpath,fname)=os.path.split(path)
        fpath=os.path.join(find_path,fname)
        if os.path.isfile(fpath):
            return fpath
        else:
            return ""
    else:
        return ""

def SetWrite(path):
    try:
        with open(path,"r+") as fr:
            return path
    except PermissionError:
        try:
            os.chmod(path, stat.S_IWRITE)
            return path
        except:
            print("Can not SetWrite:"+path)
            return False

@print_func
def OpenFile(path):
    new_doc=Binding()
    try:
        new_doc.doc=new_doc.acad.Application.documents.open(path)
        return new_doc
    except:
        with open('OpenFile.bat','w') as f:
            f.write('"'+path+'"')
        run_bat=os.system('OpenFile.bat')
        for i in range(60):
            time.sleep(1)
            try:
                new_doc.get_doc()
                print(os.path.join(new_doc.path,new_doc.name))
                if path.upper() == os.path.join(new_doc.path,new_doc.name).upper():
                    return new_doc
            except:
                pass
    print("open file time out!")
    return 0
'''
def get_size(filedir):
    tree = os.walk(filedir, topdown=True)
    dirsize = 0
    for i in tree:
        nodeName = i[0]
        nodeDirs = i[1]
        nodeFiles = i[2]
        if('Zeal' in nodeName):
            continue
        for file in nodeFiles:
            dirsize = dirsize + os.path.getsize(nodeName+'\\'+file)
    return dirsize
'''
@print_func
def log_result(file_name,file_path,result):
    print("#".join(['file name',file_name,'file path',file_path,'result',result]))
    #conn=pymysql.connect(host="10.1.42.24",user="steven",passwd="steven!@#456",db="project_test")
    conn=pymysql.connect(host="10.1.42.131",user="steven",passwd="steven!@#456",db="project_test")
    cur=conn.cursor()
    cur.execute(u"INSERT INTO BindHelperRecord(file_name,file_path,result) VALUES(%s,%s,%s)",[file_name,file_path,result])
    conn.commit()
    cur.close()
    conn.close()

if __name__=="__main__":
    main()


