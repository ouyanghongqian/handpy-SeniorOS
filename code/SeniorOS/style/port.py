from mpython import wifi,oled
from mpython import touchPad_P,touchPad_Y,touchPad_H,touchPad_O,touchPad_N,touchPad_T
from mpython import button_a,button_b
from SeniorOS.apps.port import *
import SeniorOS.system.daylight as DayLight
import SeniorOS.system.core as Core
import time

def HomeStyleSet():
    Set("home")

def BarStyleSet():
    Set("bar")

def Set(dataName:str):
    while not button_a.is_pressed():
        oled.fill(0)
        DayLight.UITools()
        time.sleep_ms(5)
        styleNum = eval('DayLight.ListOptions(Data.System.' + dataName + 'StyleName, 18, False, "风格选择")') + 1
        options = DayLight.ListOptions(['预览风格', '风格详情', '立即应用'], 8, True, "None")
        if options == 0:
            Preview(styleNum, dataName)
        if options == 1:
            pass
        if options == 2:
            Core.DataOperation.Write(dataName + "StyleNum", str(styleNum), False, False)
            return
    return

def Preview(styleNum, dataName:str):
    while not button_a.is_pressed():
        exec("from " + dataName + " import *")
        exec(str(styleNum) + "()")
        oled.DispChar('正在预览', DayLight.AutoCenter('正在预览'), 30, 1)
        oled.DispChar('A-退出 TH-确认', DayLight.AutoCenter('A-退出 TH-确认'), 40, 1)
        oled.show()
        if touchPad_T.is_pressed() and touchPad_H.is_pressed():
            Core.DataOperation.Write(dataName + 'StyleNum', str(styleNum), False, False)
            return