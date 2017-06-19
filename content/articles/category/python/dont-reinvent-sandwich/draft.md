今年的 Pycon Taiwan，有一篇我滿感興趣的演講：Don't Reinvent Sandwich - Python Decorator and Context Manager，講者是蕭聖穎先生。

> 該演講的 [投影片](https://drive.google.com/file/d/0Bz8Kfu_94VuJcVo1a1drQjhReU0/view) 和講者的 [Facebook](https://www.facebook.com/syhsiao0917?ref=ts&fref=ts)。

由於我對於語言本身的設計和使用慣例非常感興趣，所以就去朝聖了一下。講題的主旨大略是：我們通常透過抽取一段重複出現的 **連續代碼** 成為 **函數 (function)** 或 **類別 (class)** 來重複利用他，避免重複發明輪子。但有的時候想要抽取的部分並非 **中間** (
三明治的麵包）連續的部分，而是 **頭尾** （三明治的麵包），這個時候我們便需要使用一些其他的手法或機制來達到 reuse 的目的了。Python 正好非常友善地提供了 **裝飾器 (decorator)** 和 **環境管理器 (context manager)**，可以很容易地達成我們的目的。

這場演講給出了非常有意思的想法，尤其是裝飾器與環境管理器的互通。但很可惜的是，雖然 Python 的 decorator 和 context manager 非常有自己的特色也是許多大型專案常用的技術，但是對於初學者而言還是一個相對進階的主題，我認為初學者並不容易在這短短的四十五分鐘內了解全部的內容，所以寫了這篇文章，希望能詳細地頗析本場演講所涵蓋到的內容，期待能對大家有所幫助，不過所學慎淺，班門弄斧不免貽笑大方，那就還請講者及各路高手海涵。

本文的脈絡大致會依循講者的投影片，內容的部分也是，會有適度的補充，就容我多撈叨一兩句，而較零碎的細節就容我略過不提了。

> 另外，本文的許多例子和想法都來自 [Fluent Python](http://shop.oreilly.com/product/0636920032519.do) 這本書，這是我迄今看過最好的 Python 書籍了。

## 從檔案的開關談起

Python 的檔案操作一直都是很平易近人的，使用內建的 `open` 函數來開啟檔案並且獲得回傳的 **檔案物件 (file object)**，最後透過檔案物件的 `close` 方法關閉檔案，大概像是這樣子：

```python
fp = open(file_name, 'w')

# do somethings here

fp.close() # 這行很容易被遺忘
```

這段 code 沒有什麼大不了的，但是人難免會有疏漏，如果我們忘記關閉檔案這個動作，可能會引發許多不良的後果。不過這種失誤還算是比較明顯的，如果我們考慮到 `# do somethings here` 這段代碼可能會引發 **例外(exception)** 的話，這種開關檔案的方式顯然還是有待加強，我們該如何應對呢？基本上加入例外的捕捉即可，如下：

```python
fp = open(file_name, 'w')
try:
    # do somethings here
finally:
    fp.close()
```

這下我們的檔案物件無論如何都會被關閉了，可是... 這樣的代碼好醜啊！有沒有比較優雅，比較 Pythonic 的寫法呢？

當然是有的，只要受過專業的 Python 訓練，大家都知道可以使用 `with` 述句：

```python
with open(file_name, 'w') as fp:
    # do somethings here
```

太好了，原本看起來很複雜的結構霎時之間變得很單純，檔案在 `open` 之後被開啟，然後我們切進 `with` 述句的 **suite** 中做事，Python 會在離開 `with` 區塊的時候自動處理檔案的關閉，無論例外是否在區塊內發生。有的人可能會覺得很神奇，這是怎麼做到的？那剛好就是本文的主題之一：環境管理器。

不過更值得我們注意的不只是代碼的簡潔和穩定性，而是 **可被重複利用性**。試想：顯性的 `open/close` 結構要怎麼重複利用呢？我們能將之抽取為一個 function 嗎？看起來的確是困難重重，因為我們想要抽取的不再是中間那連續的部分，而是頭尾那分離的部分，我們想要重用三明治的麵包！相對來說，`with` 述句和環境管理器就提供了我們一個可以重複利用頭尾的機制，我們可以重複地利用 `with open` 來套用到每一段需要開關檔案的代碼上。

> 請讀者好好思考為什麼後面的這種結構能夠做到重複利用而前者不行，這也是本文的關鍵之處！

## 裝飾器 (decorator)

裝飾器是一種可以做到重複利用頭尾的機制，我們簡單地來介紹一下裝飾器的用法和寫法。

### 裝飾器的用法

考慮到以下兩個函數：

```python
import time
    
def snooze(s):
    """等待s秒"""
    time.sleep(s)
    
def sum_of_square(numbers):
    """計算平方和"""
    return sum([n**2 for n in numbers])
```

如果今天希望能夠測量這兩個函數的執行時間並將之印出，我們可能會想要修改一下我們的函數：

```python
import time
    
def snooze(s):
    """等待s秒"""
    t0 = time.time()
    time.sleep(s)
    elapsed = time.time()-t0
    print('Run snooze({}): {}'.format(s, elapsed))
    
def sum_of_square(numbers):
    """計算平方和"""
    t0 = time.time()
    result = sum([n**2 for n in numbers])
    elapsed = time.time()-t0
    print('Run sum_of_square({}): {}'.format(numbers, elapsed))
    return result
```

天阿，才兩個函數就迫使我們大費周章地逐一修改，如果我們有更多的函數需要測量時間豈不累死人嗎？我們多希望將這些共有的部分給抽取出來呢！假設我們有一個叫做 `clock` 的裝飾器，只要被他修飾過的函數就會自我計時並且印出時間那不是很棒嗎！不過在我們學會如何寫出這樣一個裝飾器之前，我們先來看看應該怎麼使用這樣的裝飾器，在 Python 中，我們都是這樣做的：

```python
import time

@clock
def snooze(s):
    """等待s秒"""
    time.sleep(s)
    
@clock
def sum_of_square(numbers):
    """計算平方和"""
    return sum([n**2 for n in numbers])
```

在函數的定義上方加上一行 `@裝飾器名稱` 就可以將我們的函數裝飾成想要的樣子了，這其實一點都不神奇，上面的做法跟：

```python
import time

def snooze(s):
    """等待s秒"""
    time.sleep(s)

snooze = clock(snooze)
    
def sum_of_square(numbers):
    """計算平方和"""
    return sum([n**2 for n in numbers])

sum_of_square = clock(sum_of_square)
```

是一模一樣的，使用 `@` 的做法只是 Python 中的甜頭語法。

其實裝飾器說穿了也就是一個函數！以下是我給出的一個定義：

```
裝飾器是一個函數，他能接收一個函數作為參數，並且回傳一個修飾過的函數
```

而通常這個修飾過的函數也會被賦值給原本的函數變數，意思是我們通常不會為修飾過的函數另取名稱，而會沿用原來的名字：

```python
# 通常不會為修飾過的函數另娶名稱
clock_snooze = clock(snooze)
clock_sum_of_square = clock(sum_of_square)

# 通常會使用原本的名稱
snooze = clock(snooze)
sum_of_square = clock(sum_of_square)
```

之所以如此是因為我們希望這個過程看起來是 **修飾** 而非 **取代**（即使在實際作法上我們是用取代的），我們希望使用者在呼叫函數時能夠使用相同的名稱來呼叫。

### 裝飾器的寫法

接下來我們要關心的是如何寫出 `clock` 這個裝飾器。

首先，根據定義，裝飾器是一個函數且能接收一個函數作為參數：

```python
def clock(func):
    # ...
```

而我們要回傳一個修飾過的函數，而這個函數看起來是修改原本的函數而來的，但其實我們是定義了一個新的函數來取代原本的函數:

```python
def clock(func):
    def new_func(...):
        """裝飾過的函數"""
        # ...
    return new_func
```

接著為了讓新的函數 `new_func` 和原本的函數有相同的回傳值，我們必須在新的函數中呼叫舊的函數（如此才會有相似的行爲，畢竟我們是要修飾！）：

```python
def clock(func):
    def new_func(...):
        """裝飾過的函數"""
        result = func(...)
        return result
    return new_func
```

這邊還有一個問題是，裝飾器並不知道自己要裝飾怎麼樣的函數，有的函數可能只有一個參數，有的有很多個，有的函數可能只有位置參數，有的函數卻有關鍵字參數。還好 Python 有 `*` 和 `**` 可以幫助我們處理任意數量和形式的參數：

```python
def clock(func):
    def new_func(*args, **kwargs):     # 使用星號讓新的函數能夠接受任意參數，換句話說能讓裝飾器裝飾任意函數
        """裝飾過的函數"""
        result = func(*args, **kwargs) # 呼叫原本的函數時也使用星號來進行參數拆解
        return result
    return new_func
```

> 此步驟是裝飾器成立的關鍵，不是很好理解，請讀者多多琢磨

好了，到這裡我們已經讓修飾過的函數跟原本的函數有一模一樣的行為了，接下來我們只要加上測量時間和打印的功能即可：

```python
def clock(func):
    def new_func(*args, **kwargs):
        """裝飾過的函數"""
        t0 = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - t0
        
        # func 的 __name__ 屬性儲存著函數的名字
        name = func.__name__
        
        # 將呼叫時的參數值轉為可印出的字串
        arg_strs = [repr(arg) for arg in args]
        kwarg_strs = ['{}={}'.format(key, value) for key, value in kwargs.items()]
        argstr = ','.join(arg_strs + kwarg_strs)
        
        print('Run {}({}): {}'.format(name, argstr, elapsed))
        return result
    return new_func
```

大功告成！現在我們擁有了一個可以裝飾任何函數的測時裝飾器 `clock` 了。

> 由於 `clock` 還必須印出呼叫的函數名稱和參數值，所以會稍微複雜一點，其實一些單純一點的裝飾器寫起來是很簡單的，大家千萬不要害怕。

### 使用 wraps 來改善裝飾器

現在這個 `clock` 還不夠完美，為什麼呢？

```python
# 這裡的 snooze 是用 clock 裝飾過的版本
>>> snooze.__name__
'new_func'
>>> snooze.__doc__
 
```

我們發現雖然我們用 `snooze` 這個變數來裝著裝飾過的函數，但這個函數骨子裡的名稱和文件字串都是新函數的並非原本函數的，這對於某些情境下會造成困擾，例如使用者想要查詢 `snooze` 的使用方法時：

```python
>>> help(snooze)

Help on function new_func in module __main__:

new_func(*args, **kwargs)
```

卻會得到不預期的結果，要修正這個問題就要設法將原函數的屬性複製到新函數裡，在 `functools` 模組中有一個裝飾器 `wraps`（哈哈，也是裝飾器）可以幫助我們完成任務：

```python
from functools import wraps

def clock(func):
    @wraps(func) # wraps 會將 func 的屬性抄到 new_func 裡讓 new_func 看起來跟 func 一模一樣
    def new_func(*args, **kwargs):
        """裝飾過的函數"""
        t0 = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - t0
        name = func.__name__
        arg_strs = [repr(arg) for arg in args]
        kwarg_strs = ['{}={}'.format(key, value) for key, value in kwargs.items()]
        argstr = ','.join(arg_strs + kwarg_strs)
        print('Run {}({}): {}'.format(name, argstr, elapsed))
        return result
    return new_func
```

### 帶有參數的裝飾器

接著讓我們來看看一個稍微不同的裝飾器，裝飾：

```python
@tag('div')
@tag('p')
def content():
    print('content line')
```

使用：

```html
>>> content()
<div>
<p>
content line
</p>
</div>
```

`tag` 這個裝飾器可以在原函數的輸出前後印出指定的 html tag 頭尾，我們要來研究兩個點：

1. 如何寫出帶有參數的裝飾器
2. 裝飾器的堆疊

我們直接來觀察他是怎麼一步一步被寫出來的，首先根據裝飾器的定義，我們會寫出：

```python
def tag(func):
    @wraps(func)
    def new_func():
        # do somethings before
        func()
        # do somethings after
    return new_func
```

> 在這個例子中我們不處理參數也不處理回傳值，原因是這個裝飾氣要裝飾的函數都是屬於無參數且無回傳值的。

接著我們開始進行裝飾，把印出 tag 的動作加上去：

```python
def tag(func):
    @wraps(func)
    def new_func():
        print('<{}>'.format(TAG_NAME))
        func()
        print('</{}>'.format(TAG_NAME))
    return new_func
```

現在問題來了，我們要如何傳遞 `TAG_NAME` 進去給 `new_func` 呢？ 有些人覺得是這樣：

```python
def tag(func, name):
    @wraps(func)
    def new_func():
        print('<{}>'.format(name))
        func()
        print('</{}>'.format(name))
    return new_func
```

這樣會造成一個問題，我們的確可以這樣裝飾 `content`：

```python
content = tag(content, 'p')
```

但卻沒辦法寫成 `@` 的形式，原因是 `@` 後面跟著的裝飾器函數必須是個單參數函數。

要解決這個問題，我們可以製造另一個函數，此函數會回傳真正的裝飾器：

```python
def tag(name):
    def deco(func): # 這個才是真正的裝飾器，為了把 tag 讓給更上一層的函數，這裡我們使用 `deco` 這個名字
        @wraps
        def new_func():
            print('<{}>'.format(name))
            func()
            print('</{}>'.format(name))
        return new_func
     return tag
```

我們把結構多加了一層，當我們呼叫 `tag(TAG_NAME)` 時，會得到一個真正的裝飾器，接著才呼叫該裝飾器來得到一個裝飾後的函數：

```python
ptag = tag('p') # ptag 才是真正的裝飾器
content = ptag(content)

# 或是使用 @ 的語法寫出來
@ptag
def content():
    print('content line')
    
# 或直接在 @ 的那一行呼叫 tag 製造真正的裝飾器
@tag('p') # 這一行相當於 @ptag，也就是說 tag('p') 才是直接作用的裝飾器，tag 只是製造裝飾器的函數
def content():
    print('content line')
```

### 裝飾器的堆疊

接著我們討論到裝飾器的堆疊，我們發現可以同時用若干個裝飾器去裝是一個函數，其裝飾的順序是由裡而外，這是非常顯而易見的，當我們看到：

```python
@tag('div')
@tag('p')
def content():
    print('content line')
```

其實相當於：

```python
divtag = tag('div')
ptag = tag('p')

content = content(divtag(ptag(content)))
```

`content` 會先被 `ptag` 也就是 `tag('p')` 裝飾，接著才被 `divtag` 也就是 `tag('div')` 裝飾。其實只要我們將裝飾器的甜頭語法還原回去，便很容易理解裝飾器的原理和行為。

這邊我們也順帶了解到一種用法，我們可以透過 `tag('p')` 和 `tag('div')` 先行製造常用的裝飾器來使用，比如我們以後就可以直接這樣寫了：

```python
@divtag
@ptag
def content():
    print('content line')
```

### 裝飾器的範例

裝飾器有相當多的用途和範例，這邊作者就不多做說明了，讀者可以參考講者的 [投影片](https://drive.google.com/file/d/0Bz8Kfu_94VuJcVo1a1drQjhReU0/view)，裡面提到的應用包含：

* function log
* top function exception
* click_

### 常用的內建裝飾器

除了我們自行撰寫的裝飾器之外，Python 也有需多內建的裝飾器，例如內建函數中就有：

* `property`
* `classmethod`
* `staticmethod`

這三種用來裝飾 **類別方法** 的裝飾器。

而在 `functools` 中也有三個很實用的裝飾器，分別是：

* `functools.wraps`
* `functools.lru_cache`
* `functools.singeldispatch`

除了我們介紹過的 `wraps` 之外，這裡也順帶介紹一下講者有提到的 `lru_cache`。

### functools.lru_cache

這邊講者有個小小錯誤（應該是不小心記錯了，其實每次這種縮寫我是根本不記得到底指的是什麼），lru cache 的意思並非 latest-recently-used cache（最近一次的常用快取），而是 least-recently-used（最小的常用快取），意思是他並不會緩存所有的項目，只會記憶最近一段時間的常用項目，太久沒有被讀取的項目會被移出緩存區。

我們來看一個使用範例：

```python
@clock # 使用前面我們自行定義的 clcok 裝飾器
def fibonacci(n):
    """求取費氏數列的第n項"""
    if n < 2:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
```

>  這裡我使用的是 Fluent Python 一書中的範例，講者在投影片中也有一個 `heavy_job` 的範例，大家可以自行參考。

以下是使用範例：

```python
>>> fibonacci(6)
Run fibonacci(1): 9.5367431640625e-07
Run fibonacci(0): 1.9073486328125e-06
Run fibonacci(2): 0.0001251697540283203
Run fibonacci(1): 9.5367431640625e-07
Run fibonacci(3): 0.0001609325408935547
Run fibonacci(1): 9.5367431640625e-07
Run fibonacci(0): 0.0
Run fibonacci(2): 3.695487976074219e-05
Run fibonacci(4): 0.00023412704467773438
Run fibonacci(1): 1.1920928955078125e-06
Run fibonacci(0): 0.0
Run fibonacci(2): 3.409385681152344e-05
Run fibonacci(1): 1.1920928955078125e-06
Run fibonacci(3): 7.200241088867188e-05
Run fibonacci(5): 0.00033593177795410156
Run fibonacci(1): 0.0
Run fibonacci(0): 1.1920928955078125e-06
Run fibonacci(2): 2.8133392333984375e-05
Run fibonacci(1): 9.5367431640625e-07
Run fibonacci(3): 6.389617919921875e-05
Run fibonacci(1): 0.0
Run fibonacci(0): 9.5367431640625e-07
Run fibonacci(2): 3.504753112792969e-05
Run fibonacci(4): 0.00013399124145507812
Run fibonacci(6): 0.0005078315734863281
8
```

由於 `fibonacci` 是一個遞迴函數，所以我們發現中間有不少計算重複了，如果要避免這種情形我們可以這樣做：

```python
dict = {}

@clock # 使用前面我們自行定義的 clcok 裝飾器
def fibonacci(n):
    """求取費氏數列的第n項"""
    if n in dict:
        pass
    elif n < 2:
        dict[n] = n
    else:
        dict[n] = fibonacci(n-1) + fibonacci(n-2)
    return dict[n]
```

但這樣做還不夠好，因為原本簡潔的函數現在變得很複雜，但使用 `lru_cache` 就能很好地解決這個問題：

```python
from functools import lru_cache

@lru_cache()
@clock # 使用前面我們自行定義的 clcok 裝飾器
def fibonacci(n):
    """求取費氏數列的第n項"""
    if n < 2:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
```

首先要注意的是，`lru_cache` 是帶參數的裝飾器，所以我們必須先呼叫他來取得直接作用的裝飾器，只是它允許不給參數。

結果：

```python
>>> fibonacci(6)
>>> Run fibonacci(1): 1.1920928955078125e-06
Run fibonacci(0): 2.1457672119140625e-06
Run fibonacci(2): 0.00012111663818359375
Run fibonacci(3): 0.00014090538024902344
Run fibonacci(4): 0.0001609325408935547
Run fibonacci(5): 0.0001819133758544922
Run fibonacci(6): 0.0002009868621826172
```

很顯然地，對於費氏數列的每一項計算我們都只需要呼叫一次函數，這是因為計算過的結果已經被緩存起來了，當重複的運算要被執行時，`lru_cache` 會先從快取中尋找計算的結果。