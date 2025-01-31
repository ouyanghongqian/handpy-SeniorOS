import time
import os
import framebuf
import network
import gc
import time
import urequests
import ujson
from machine import unique_id
from mpython import *
import SeniorOS.data.main as Data
# 适用于data下fos扩展名文件的信息读写操作
# 将大部分使用了init_file write_file类函数而只对data文件夹下的数据作读写的代码替换为此处代码
# 初始化函数
class DataCtrl:
    # 初始化函数，传入文件夹路径
    def __init__(self,dataFolderPath): # 文件夹传参结尾必须要有反斜杠！！！
        self.data={}
        self.dataFolderPath=dataFolderPath
        eval("[/EnableDebugMsg('Core.DataCtrl.__init__')/]");print([f for f in os.listdir(dataFolderPath) if f.endswith('.sros')])
        for i in [f for f in os.listdir(dataFolderPath) if f.endswith('.sros')]:
            with open(dataFolderPath+i,'r',encoding='utf-8')as f:
                self.data[i.strip('.sros')]=f.read().strip('\r')
                eval("[/EnableDebugMsg('Core.DataCtrl.__init__')/]");print(self.data[i.strip('.sros')])
        # 反正几乎是内部API 所以编码 命名规则 换行符采用 自己手动改改（
        eval("[/EnableDebugMsg('Core.DataCtrl.__init__')/]");print(self.data)
    # 获取数据
    def Get(self,dataName):
        return self.data[dataName]
    # 写入数据
    def Write(self,dataName,dataValue,singleUseSet=False,needReboot=False):
        if singleUseSet: # singleUseSet参数:一次性设置 不会实际写入文件 此选参为True时 needReboot不生效
            self.data[dataName]=dataValue
            return
        with open(self.dataFolderPath+dataName+'.sros','w',encoding='utf-8') as f:
            f.write(dataValue)
        if not needReboot: #needReboot参数:当该值为True时 不修改实际运行值 特别适用于类似 开机需要根据config作init的程序使用
            self.data[dataName]=dataValue  
        try:
            exec("Data.System." + dataName + "=" + dataValue)
        except:
            exec("Data.User." + dataName + "=" + dataValue)      
DataOperation=DataCtrl("/SeniorOS/data/variable/")

# 文件/路径 格式工厂
class File_Path_Factory:

    # 将所有的斜杠替换为反斜杠 便于统一路径
    def Replace2Backslash(path):
        return path.replace("\\","/")

    # 判断文件是否存在
    # 传入一绝对路径 返回1布尔值
    def FileIsExist(filePath:str)->bool:
        filePath=File_Path_Factory.Format.Replace2Backslash(filePath)
        if filePath[-1] in os.listdir("/"+filePath[:-1]):return True
        else:return False

    # 判断路径指向的文件对象是否是目录
    # 传入一绝对路径 返回1布尔值
    def IsDir(filePath:str)->bool:
        # 检查st_mode(第一项)中文件类型位
        try:return os.stat(filePath)[0] & 0o170000 == 0o040000
        # 如异常代表路径无效或不是目录
        except:return False

# 获取日期 ByGxxk
class GetTime:
    Year=lambda:time.localtime()[0]
    Month=lambda:time.localtime()[1]
    Week=lambda:time.localtime()[6]
    Day =lambda:time.localtime()[2]
    Hour=lambda:time.localtime()[3]
    Min =lambda:time.localtime()[4]
    Sec =lambda:time.localtime()[5]

def FullCollect():
    # 反复进行collect函数直至达到极限
    # 此代码来自 TaoLiSystem
    m=gc.mem_free()
    while True:
        gc.collect()
        if m != gc.mem_free():
            m = gc.mem_free()
        else:
            return m

# 获取设备ID
def GetDeviceID(wifiStaObj=network.WLAN(network.STA_IF),
                mode=1
        ):
    if mode==0:return "".join(str(wifiStaObj.config('mac'))[2:len(str(wifiStaObj.config('mac')))-1].split("\\x"))
    elif mode==1:return "".join(str(unique_id())[2:len(str(unique_id()))-1].split("\\x"))

# 支持2算法的截图
# 分别为 直接复制缓冲区数据(CopyFrameBuf) 和 枚举缓冲区数据(Enumerate)
# 在Enumerate中 又细分为 速度优先(fast) 与 内存占用最小(ram)
# 这里Enumerate部分使用的算法取决于构建阶段 对本代码作EXPR操作时 constData["screenMethod"] 的值是 fast 还是 ram
class Screenshot:
    def CopyFramebuf(path,oledObj=__import__("mpython").oled):
        bufb=bytearray(128*64)
        with open(path,"wb")as f:
            f.write(b"P4\n128 64\n")
            buf=framebuf.FrameBuffer(bufb,128,64,framebuf.MONO_HLSB)
            buf.blit(oledObj.buffer,0,0)
            f.write(bufb)
    def Enumerate(path,oledObj=__import__("mpython").oled):# 以「枚举」为核心 的算法
        if eval("[/Const('screenshotMethod')/]")=="fast": # 速度优先
            with open(path, 'wb') as f:
                f.write(b'P4\n128 64\n')
                for y in range(128):
                    row_data = bytearray(8) #缓冲区
                    for x in range(64):row_data[x//8]|=(oledObj.pixel(x, y))<<7-(x%8) #循环 算偏移量 然后转格式 写到缓冲区内
                    f.write(row_data)
        elif eval("[/Const('screenshotMethod')/]")=="ram":# RAM优先
            buffer = bytearray(1024)  # 创建缓冲区
            # 获取屏幕像素状态
            for y in range(64):
                for x in range(128):
                    buffer[x//8+y*16]|=oledObj.pixel(x,y)<<7-(x%8)
            # 保存为PBM文件
            with open('screenshot.pbm', 'wb') as f:
                # 写入PBM文件头
                f.write(b'P4\n128 64\n')
                f.write(buffer)  # 将缓冲区数据写入PBM文件

class BatteryLevelFetcher:
    """
    获取电池剩余电量函数，存储当前电池剩余电量的字符串形式。
    """
    def __init__(self):
        self.bay_rvol = 3.3  # 假设这个是固定的数值
        self.bay_cvol = self.fetch_battery_level()  # 假设这个是通过某个方法获取的数值
        self.battery_level = None
        self.calculate_battery_level()
    def fetch_battery_level(self):
        return parrot.get_battery_level()  # 假设这个是通过某个方法获取的数值
    def calculate_battery_level(self):
        if self.bay_cvol is not None:
            bay_rem = (self.bay_cvol / 1000) / self.bay_rvol * 100
            self.battery_level = "{:.1f}".format(bay_rem)
        else:
            self.battery_level = None

def Tree(path="/",prt=print,_tabs=0):
    lst=os.listdir(path)
    dirs=[]
    files=[]
    l=0
    for i in lst:
        pti=path+'/'+i
        if os.stat(pti)[0] & 0x4000:
            dirs.append(i)
        else:
            files.append(i)
        l+=1
    lk="├"
    ldirs=len(dirs)
    for n,i in enumerate(dirs+files,1):
        if n==l:
            lk="└"
        prt("│"*_tabs+lk+i)
        if n<ldirs:
            Tree(path+'/'+i,prt,_tabs+1)
