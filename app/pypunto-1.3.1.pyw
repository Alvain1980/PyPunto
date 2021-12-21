# coding=utf-8

import time
import py_win_keyboard_layout
import pyperclip
import wx
import wx.adv
from pynput import keyboard
from pynput.keyboard import Controller, Key, KeyCode
import pathlib

#### Горячие клавиши - комбинации можно изменить для настройки под себя, не все комбинации всегда работают, 
# например, у меня pause локально работает, а при подключении по RDP - нет ####

# KeyCode клавиши можно узнать через сервис https://keycode.info/

# приведение текста к верхнему регистру
TEXT_UP = [Key.ctrl_l, Key.alt_l, Key.page_up]
# приведение текста к нижнему регистру
TEXT_LOW = [Key.ctrl_l, Key.alt_l, Key.page_down]
# приведение текста к противоположному регистру
TEXT_SWAP_CASE = [Key.ctrl_l, Key.alt_l, Key.insert]
# переключение языка по выделению или всей строки
TEXT_SEL_OR_LINE_SWITCH = [Key.scroll_lock]

# Задержка (с) для обработки ОС событий нажатий клавиш
DELAY = 0.05

####### Дальше текст не менять !!! #######

eng = '`1234567890-=qwertyuiop[]asdfghjkl;\'\\zxcvbnm,./~!@#$%^&*()_+QWERTYUIOP{}ASDFGHJKL:"|ZXCVBNM<>?'
rus = 'ё1234567890-=йцукенгшщзхъфывапролджэ\\ячсмитьбю.Ё!"№;%:?*()_+ЙЦУКЕНГШЩЗХЪФЫВАПРОЛДЖЭ/ЯЧСМИТЬБЮ,'

version = '1.3.1'

text_up_hint = '+'.join([x._name_ for x in TEXT_UP])
text_low_hint = '+'.join([x._name_ for x in TEXT_LOW])
text_swap_hint = '+'.join([x._name_ for x in TEXT_SWAP_CASE])
text_line_hint = '+'.join([x._name_ for x in TEXT_SEL_OR_LINE_SWITCH])

TRAY_TOOLTIP = (
    f'PyPunto v. {version}\n'
    f'A: <{text_up_hint}>\n'
    f'a: <{text_low_hint}>\n'
    f'Aa->aA: <{text_swap_hint}>\n'
    f'Нуы->Yes: <{text_line_hint}>\n'
    )

TRAY_ICON = str(pathlib.Path(__file__).parent.absolute()) + '\\pypunto.png'

kb = Controller()

def str_is_empty(str):
    return (str in (None, '') or not str.strip())

def str_isnt_empty(str):
    return not str_is_empty(str)

def create_menu_item(menu, label, func):
    item = wx.MenuItem(menu, -1, label)
    menu.Bind(wx.EVT_MENU, func, id=item.GetId())
    menu.Append(item)
    return item
class TaskBarIcon(wx.adv.TaskBarIcon):
    def __init__(self, frame):
        self.frame = frame
        self.on_exit_event = None
        super(TaskBarIcon, self).__init__()
        self.set_icon(TRAY_ICON)

    def CreatePopupMenu(self):
        menu = wx.Menu()
        # create_menu_item(menu, 'Site', self.on_hello)
        # menu.AppendSeparator()
        create_menu_item(menu, 'Выход', self.on_exit)
        return menu

    def set_icon(self, path):
        icon = wx.Icon(path)
        self.SetIcon(icon, TRAY_TOOLTIP)

    def on_exit(self, event):
        if self.on_exit_event:
            self.on_exit_event(event)
        wx.CallAfter(self.Destroy)
        self.frame.Close()
    
    def set_tray_lmbc_event(self, event):
        self.Bind(wx.adv.EVT_TASKBAR_LEFT_DOWN, event)
    
    def set_tray_exit_event(self, event):
        self.on_exit_event = event

class App(wx.App):
    def OnInit(self):
        frame=wx.Frame(None)
        self.SetTopWindow(frame)
        self.pressed_keys = set()
        self.hotkeys_monitor = keyboard.Listener(on_press=self.on_press, on_release=self.on_release)
        self.tbi = TaskBarIcon(frame)
        self.tbi.set_tray_lmbc_event(self.on_tray_lmbc)
        self.tbi.set_tray_exit_event(self.on_exit)
        self.hotkey_processing = False
        self.hotkeys_monitor.start()
        self.hotkeys_functions = {
            frozenset(TEXT_UP): self.text_up,
            frozenset(TEXT_LOW): self.text_low,
            frozenset(TEXT_SWAP_CASE): self.text_swap_case,
            frozenset(TEXT_SEL_OR_LINE_SWITCH): self.switch_sel_or_line,
        }
        return True

    def get_clipboard_text(self):
        clipboard_content = pyperclip.paste()
        return clipboard_content

    def set_clipboard_text(self, data):
        pyperclip.copy(data)

    def transcode_text(self, text):
        cur_lang = ''
        result = ''
        for i, c in enumerate(text):
            if (c in rus) and (c in eng):
                if cur_lang == 'rus':
                    result = result + eng[rus.index(c)]
                elif cur_lang == 'eng':
                    result = result + rus[eng.index(c)]
                else:
                    result = result + eng[rus.index(c)]
            elif c in rus:
                result = result + eng[rus.index(c)]
                cur_lang = 'rus'
            elif c in eng:
                result = result + rus[eng.index(c)]
                cur_lang = 'eng'
            else:
                result = result + c
        
        # если последний опредленный язык был русский, то переключаем на английский, если английский, то на русский
        if cur_lang == 'rus':
            self.set_english()
        if cur_lang == 'eng':
            self.set_russian()

        return result

    def set_russian(self):
        time.sleep(DELAY)
        py_win_keyboard_layout.change_foreground_window_keyboard_layout(0x04190419)
        time.sleep(DELAY)

    def set_english(self):
        time.sleep(DELAY)
        py_win_keyboard_layout.change_foreground_window_keyboard_layout(0x04090409)
        time.sleep(DELAY)

    def copy_selection(self):
        # сбрасываем буфер обмена, т.к. если нет выделения, то при ctrl+v он останется неизменным (в некотором ПО)
        self.set_clipboard_text('')
        with kb.pressed(Key.ctrl_l):
            kb.tap('c')
        time.sleep(DELAY)
        text = self.get_clipboard_text()
        return text

    def paste_clipboard(self):
        with kb.pressed(Key.ctrl_l):
            kb.tap('v')
        time.sleep(DELAY)

    def get_keycode(self, key):
        # получаем KeyCode нажатой клавиши (работает, только если клавиша не задана через char)
        vk = None
        if isinstance(key, Key):
            vk = key.value.vk
        elif isinstance(key, KeyCode):
            vk = key.vk        
        return vk

    def is_hotkeys_pressed(self, hotkeys):
        # проверяем, что нажаты все кнопки заданной комбинации и не нажаты при этом "лишние" -
        # на случай, если заданы горячие клавиши, например, на "F12" и на "ctrl+F12". 
        res = all([self.get_keycode(key) in self.pressed_keys for key in hotkeys]) and (len(self.pressed_keys) == len(hotkeys))
        return res

    def release_keys(self):
        for vk in self.pressed_keys:
            if vk:
                key = keyboard.KeyCode(vk=vk)
                kb.release(key)
        time.sleep(DELAY)

    def select_line(self):
        kb.tap(Key.end)
        time.sleep(DELAY)
        with kb.pressed(Key.shift):
            kb.tap(Key.home)
            time.sleep(DELAY)

    def text_switch_functions(self, function):
        saved_clipboard = self.get_clipboard_text()
        text_processed = None
        text = None
        # сначала получаем текст выделенного фрагмента, если нажата клавиша перевода последнего введенного текста
        if function == 'selection_or_line':
            text = self.copy_selection()
            # Если текст не выделен, выделяем строку
            if str_is_empty(text):
                self.select_line()
        # если выше еще не копировали текст, то копируем
        if str_is_empty(text):
            text = self.copy_selection()

        # если выделение было сделано и скопировали текст в буфер обмена, начинаем "перевод"
        if str_isnt_empty(text):
            if function == 'selection_or_line':
                text_processed = self.transcode_text(text)
            elif function == 'upper':
                text_processed = text.upper()
            elif function == 'lower':
                text_processed = text.lower()
            elif function == 'swapcase':
                text_processed = text.swapcase()

        if text_processed:
            self.set_clipboard_text(text_processed)
            self.paste_clipboard()
            # восстанавливаем буфер обмена
            self.set_clipboard_text(saved_clipboard)        

    def switch_sel_or_line(self, hotkeys):
        self.text_switch_functions('selection_or_line')

    def text_up(self, hotkeys):
        self.text_switch_functions('upper')

    def text_low(self, hotkeys):
        self.text_switch_functions('lower')

    def text_swap_case(self, hotkeys):
        self.text_switch_functions('swapcase')

    def on_press(self, key):
        # получаем KeyCode нажатой клавиши
        vk = self.get_keycode(key)
        self.pressed_keys.add(vk)
    
    def on_release(self, key):
        # во время обработки комбинации горячих клавиш эмулируются нажатия, поэтому ставим флаг, чтобы игнорировать реакцию на них
        if not self.hotkey_processing:
            # пока нажал и держишь клавиши модификаторы (shift, ctrl, alt, ...), 
            # система создает события однократных нажатий с заданной системой скоростью,
            # поэтому запуск обработчика будем делать по событию отпускания кнопки.
            # при этом событие отпускания не возникает, что свидетельствует об удерживании кнопки.
            for hotkeys in self.hotkeys_functions:
                if self.is_hotkeys_pressed(hotkeys):
                    self.hotkey_processing = True
                    self.release_keys()
                    self.pressed_keys = set()
                    self.hotkeys_functions[hotkeys](hotkeys)

            # если уже начали отпускать кнопки, чистим сохраненный набор нажатых кнопок, 
            # чтобы не сработали наборы, состоящие из меньшего кол-ва кнопок
            self.pressed_keys = set()
            self.hotkey_processing = False
        
    def on_tray_lmbc(self, event):
        # по левой кнопке мыши на иконку в трее пока ничего не делаем
        pass
    
    def on_exit(self, event):
        self.hotkeys_monitor.stop()

def main():
    app = App(False)
    app.MainLoop()

if __name__ == '__main__':
    main()
