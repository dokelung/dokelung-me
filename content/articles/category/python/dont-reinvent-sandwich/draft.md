# 別重複發明三明治：Python 的裝飾器和環境管理器

今年的 Pycon Taiwan，有一篇我滿感興趣的演講：Don't Reinvent Sandwich - Python Decorator and Context Manager，講者是蕭聖穎先生。

> 該演講的 [投影片][Slides] 和講者的 [Facebook][Speeker FB]。

由於我對於語言本身的設計和使用慣例非常感興趣，所以就去朝聖了一下。講題的主旨大略是：我們通常透過抽取一段重複出現的 **連續代碼** 成為 **函數 (function)** 或 **類別 (class)** 來重複利用他，避免重複發明輪子。但有的時候想要抽取的部分並非 **中間** (
三明治的麵包）連續的部分，而是 **頭尾** （三明治的麵包），這個時候我們便需要使用一些其他的手法或機制來達到 reuse 的目的了。Python 正好非常友善地提供了 **裝飾器 (decorator)** 和 **環境管理器 (context manager)**，可以很容易地達成我們的目的。

這場演講給出了非常有意思的想法，尤其是裝飾器與環境管理器的互通。但很可惜的是，雖然 Python 的 decorator 和 context manager 非常有自己的特色也是許多大型專案常用的技術，但是對於初學者而言還是一個相對進階的主題，我認為初學者並不容易在這短短的四十五分鐘內了解全部的內容，所以寫了這篇文章，希望能詳細地頗析本場演講所涵蓋到的內容，期待能對大家有所幫助，不過所學慎淺，班門弄斧不免貽笑大方，那就還請講者及各路高手海涵。

本文的脈絡大致會依循講者的投影片，內容的部分也是，會有適度的補充，就容我多撈叨一兩句，而較零碎的細節就容我略過不提了。

> 另外，本文的許多例子和想法都來自 [Fluent Python][Fluent Python] 這本書，這是我迄今看過最好的 Python 書籍了。

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

裝飾器有相當多的用途和範例，這邊作者就不多做說明了，讀者可以參考講者的 [投影片][Slides]，裡面提到的應用包含：

* function log
* top function exception
* click_
* cache_json(mock function by modified file)

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
Run fibonacci(1): 1.1920928955078125e-06
Run fibonacci(0): 2.1457672119140625e-06
Run fibonacci(2): 0.00012111663818359375
Run fibonacci(3): 0.00014090538024902344
Run fibonacci(4): 0.0001609325408935547
Run fibonacci(5): 0.0001819133758544922
Run fibonacci(6): 0.0002009868621826172
8
```

很顯然地，對於費氏數列的每一項計算我們都只需要呼叫一次函數，這是因為計算過的結果已經被緩存起來了，當重複的運算要被執行時，`lru_cache` 會先從快取中尋找計算的結果。

`lru_cache` 的原理很簡單，他利用 字典(dictionary) 來作為緩存區，每一次的函數呼叫，都會將該次呼叫的引數當作字典的 **鍵(key)**，將其回傳值當作字典的 **值(value)**，將此鍵值對存入字典中以便下次查詢。

> 由這裡我們發現，`lru_cache` 的使用必須要注意一件事，那就是被 `lru_cache` 裝飾的函數，其所使用的引數都必須是 **可雜湊的(hashable)**。

`lru_cache` 有兩個可選的參數，一個是 `maxsize`，用以指定緩存區的大小，代表著有多少呼叫的結果會被儲存，一旦緩存被填滿，較舊的結果將會被丟棄。

另外一個參數是 `typed` ，這是個布林值，預設是 `False`。當它被設為 `True`時 ，一些同值但不同型的資料 (例如整數 `1` 與浮點數 `1.0`) 會被視為不同的緩存鍵值。

### 用裝飾器來註冊函數

接著讓我們來介紹一個小 trick，通常我們會在裝飾器中製造一個新的函數用以取代原函數以達到 **裝飾** 的效果，而為了展現與原函數相似的行為，我們會在此新函數內呼叫原函數，而裝飾的部分大致上會展現在新函數中原函數被呼叫的前後，這樣說明有點難以明白，我們直接看例子：

```python
def deco(func):
    @wraps(func)
    def new_function(*args, **kwargs):
        # 裝飾點1: 在原函數呼叫之前做些什麼...
        result = func(*args, **kwargs)
        # 裝飾點2: 在原函數呼叫之後做些什麼...
        return result
    return new_function
```

上面是一個典型的裝飾器結構，通常我們會在 `裝飾點1` 和 `裝飾點2` 這兩個地方做手腳來改變原本函數的行為，但其實還有一個地方可以利用：

```python
def deco(func):
    # 裝飾點3: 在裝飾的當下註冊函數 func ...
    @wraps(func)
    def new_function(*args, **kwargs):
        # 裝飾點1: 在原函數呼叫之前做些什麼 ...
        result = func(*args, **kwargs)
        # 裝飾點2: 在原函數呼叫之後做些什麼 ...
        return result
    return new_function
```

沒錯，我們不必等到裝飾過的新函數被呼叫了才進行裝飾的動作，我們可以在 **裝飾的當下** 立刻將原函數給註冊起來，比如說在 Flask 等 web 框架中會使用到的 url mapping 機制就是這樣完成的，我們直接來看範例：

> 這個範例中，作者寫了一個跟 `flask.Flask.route` 類似的裝飾器，但當然是簡化許多的版本。

```python
from functools import wraps

url_mapping = {}

def myroute(url):
    def deco(view_func):
        url_mapping[url] = view_func # 註冊 url 及其對應的 view function
        return view_func             # 把原函數當成修飾過的函數即可，因為這次修飾的重點在於註冊，而非改變原函數行為
    return deco
```

> 這個結構跟一開始介紹的裝飾器不大相同，讀者可能會很疑惑，但事實上，裝飾器不一定要製造並回傳一個新函數，他也可以單純的製造一個空間和時機讓我們能夠註冊要被裝飾的原函數。也就是說，有的時候裝飾不見得是改變函數行為，**記憶** 函數也可以是裝飾的一環。

有了 `myroute` 之後，我就可以用它來裝飾我所有的 **視圖函數(view function)**，並且將 url mapping 記憶在字典中：

```python
@myroute('/')
def index():
    return 'Index Page'
    
@myroute('/hello')
def hello():
    return 'Hello, World'
```

我們來看看裝飾過後製造出來的字典 `url_mapping` 長什麼樣子：

```python
>>> url_mapping
{'/': <function __main__.index>, '/hello': <function __main__.hello>}
```

很好，我們利用註冊完成了 url 映射的功能了！

### 裝飾器小結

在這篇文章的前半部，我們認識了裝飾器的基本用法與寫法，學到了用 `functools.wraps` 來完善裝飾器的做法，更了解到了帶有參數的裝飾器是如何完成的。接著，我們談及了裝飾器的範例和介紹了內建可用的幾個裝飾器，最後用裝飾器提供的額外修飾空間完成了函數註冊的功能。

其實裝飾器的應用遠不止此，其議題也不勝枚舉，包含變數範圍，non local 與 closure 的問題，有興趣的讀者可以去找尋更多有關的資料，但礙於本文篇幅及講者演講的範圍，只好忍痛割捨了。

> 其實只是作者懶了ＸＤ，非常建議大家馬上去買一本 Fluent Python，保證可以從 Luciano 大叔身上學到不少！

## 環境管理器

接著我們進入另一個主題：**環境管理器(context manager)** 或又稱 **情境管理器**。

環境管理器是一個能夠撘配 `with` 述句使用的類別，他能夠在切入環境時進行 **環境的設定** 和若干 **預處理** 的行為，並且能夠在離開環境時進行 **重置** 並做 **善後處理**（包含處理例外的發生）。

我們在 [PEP 343 -- The "with" Statement][PEP 343] 中，可以了解到 `with` 和 環境管理器的基本概念，同時裡面有點出了一個重要的概念就是：

```
with statement makes it possible to factor out standard uses of try/finally statements
```

這也是為什麼現在檔案的開關都建議使用 `with as` 的寫法了。 

### 環境管理器的寫法和用法

一個基本而標準的環境管理器是一個具備 `__enter__` 和 `__exit__` 的類別。

下面是一個用來計時的環境管理器：

```python
import time

class Clock:
    """用以計時的環境管理器"""
    
    def __enter__(self):
        print('start')
        self.t0 = time.time()
        return self
        
    def __exit__(self, exc_type, exc_value, traceback):
        print('stop')
        elapsed = time.time() - self.t0
        print('elapsed {}'.format(elapsed))
        return True
```

用法：

```python
clock = Clock()  # 產生 clock 實例

with clock as clock:
    time.sleep(3)
```

效果：

```
start
stop
elapsed 3.0003809928894043
```

### 進入環境

首先，`with` 後面要跟著環境管理器的 **實例(instance)**，也就是 `Clock` 類別產生的 `clock` 物件，此時 Python 會呼叫 `clock` 的 `__enter__` 表示開始切入環境，於是印出了 `start` 字樣，這個時候 `clock` 的屬性 `t0` 也會保存著切入環境的起始時間，最後回傳自己（`clock`）並賦值給 `as` 後面的變數。

這邊有一個重點就是：`as` 後面的變數來自於 `__enter__` 的回傳值，而在許多例子中，`__enter__` 會回傳自己，也就是環境管理器本身，原因是環境管理器可能身負環境管理之外的其他職責。

例如我們常見的檔案開關：

```python
with open(file_name, 'w') as fp:
    # do somethings here
```

`open` 函數回傳的是一個檔案物件，但他也同時被當成環境管理器使用（因為 `open` 的回傳值放在 `with` 後面，所以可以知道檔案物件就是一個環境管理器），為了能在 `with` 的子區塊中使用檔案物件，我們必須利用 `as` 將此物件賦值給 `fp`，而這個動作靠的就是讓環境管理器的 `__enter__` 回傳自己。

> 初學者常容易搞混，以為 `fp` 是呼叫 `open` 的回傳值，但其實中間隔了一層，`fp` 是透過環境管理器的 `__enter__` 拿到的，只是剛好 `__enter__` 回傳的就是環境管理器本身。

不過這裡還是要提醒大家，`__enter__` 方法是允許不回傳自己的，也就是說述句 `with A as B` 中，`A` 並不一定等於 `B`。

另外，如果在區塊內不需要使用到 `__enter__` 回傳值的話，`with` 述句也可以完全不用有 `as`，這也代表了某些情境之下，`__enter__` 不一定要有回傳值。其實，在 `Clock` 這個例子中，`clock` 物件在 `with` 中並不需要用到，我們大可省略 `__enter__` 的回傳動作和 `with as` 中的 `as` 部分。 

### 離開環境

在 `time.sleep(3)` 執行完畢之後，我們會離開 `with` 區塊，這個時候環境管理器 `clock` 的 `__exit__` 會被呼叫。於是 `stop` 被打印出來，接著 `elapsed` 在這裡被計算和印出。

這裡值得注意的是 `__exit__` 的參數和回傳值，我們從他的參數開始談起。

由於環境管理器肩負著一個重要使命：對於任何狀況都要能夠妥當地善後，並確保任何問題會被正確處理，所以必定存在著一個處理例外的機制。

當 `with` 區塊內引發了例外且該例外在區塊內沒有被捕捉，此時例外不會馬上被傳播出去，他會被當成 **參數** 傳給 `__exit__` 方法，其一是確保例外發生時，`__exit__` 方法也會運作進行善後，其二是我們能在 `__exit__` 方法中正確處理例外。

`__exit__` 一共有三個參數，分別是：

* `exc_type`: 例外類別（例如：`ZeroDivisionError`）
* `exc_value`: 例外實例 (例如：`division by zero`)
* `traceback`: traceback 物件

但如果 `with` 區塊中沒有例外發生或例外已被捕捉，上述的參數值都將會是 `None`，例如剛剛看到的 `time.sleep(3)` 這個例子。

而 `__exit__` 的回傳值代表著例外有沒有被妥善處理，若回傳 `True` 以外的值，則 `with` 區塊中若有例外發生將會被傳播出去。

### 等價代碼

為了讓讀者能夠更清楚了解環境管理器的運作，下面提供了一段不使用 `with` 的等價代碼，來展示 `clock` 這個環境管理器不搭配 `with` 時應該如何運作：

```python
clock = Clock()  # 產生 clock 實例

# 使用 with 的環境管理器
with clock as clock:
    time.sleep(3)
    
# 不使用 with 的環境管理器，此段代碼等價於上段代碼
clock = clock.__enter__()
try:
    timte.sleep(3)
except Exception as e: # 發生例外，捕捉並當成參數傳入 __exit__
    if not clock.__exit__(type(e), e, e.__traceback__) # 或可以用 clock.__exit__(sys.exc_info())
        raise e # 如果例外沒有被正確處理，將之傳播出去
else:
    clock.__exit__(None, None, None) # 沒有例外發生，例外參數值都是 None
```

### 更複雜的管理器

這裡讓我們來實做一個更複雜的環境管理器：一個新版的 `Clock`，與最初版本的不同在於，他能夠儲存多筆計時資料：

```python
import time

class Clock:
    """用以計時的環境管理器"""
    def __init__(self, name):
        self.record = {}
        self(name)
    
    def __call__(self, name):
        self.name = name
        return self
    
    def __enter__(self):
        self.t0 = time.time()
        return self
        
    def __exit__(self, exc_type, exc_value, traceback):
        elapsed = time.time() - self.t0
        self.record[self.name] = elapsed
        print(elapsed)
        
    def report(self):
        print(self.record)
```

我們來瞧瞧他是如何被使用的：

```python
with Clock('snooze 3') as clock:
    time.sleep(3)

with clock('snooze 5') as clock:
    time.sleep(5)
    
clock.report()
```

結果：

```python
3.000840902328491
5.00306510925293
{'snooze 5': 5.00306510925293, 'snooze 3': 3.000840902328491}
```

這裡有幾個重點：

1. 我們第一次使用 `Clock` 的時候，是直接在 `with` 述句中進行實例化的，這跟 `open` 的使用習慣類似。
2. `Clock` 的 `__enter__` 也是回傳傳自己，所以 `clock` 就是 `Clock()`。
3. `clock` 是可以重複利用的，第二次的 `with` 述句，我們使用了同一個環境管理器。
4. 為了讓每一次的計時可以有一個名稱，我們會傳入一個字串，同時，為了能夠使用同一個環境管理器，我們實作了 `__call__` ，讓物件也變的可呼叫，才能傳遞該字串參數。
5. 由這個例子我們發現，一個環境管理器並不一定是一個單純的環境管理器，他也能有 `__enter__` 和 `__exit__` 以外的方法，例如： `report`。

> 建議讀者去猜測、閱讀和思考檔案物件的實作方法，一定能大有收穫！

### 環境管理器的範例

環境管理器也有相當多的用途和範例，讀者可以參考講者的 [投影片][Slides]，裡面提到的應用包含：

* tempfile
* dump print to file: use `refirect_stdout`
* change loggin level
* simulation precision
* pytest test exception
* timeit（跟 `clock` 很像的應用）

### contextlib 公用程式

雖然 Python 提供了環境管理器的協定（包含 `with`、`__enter__`、`__exit__`），使得類別形式的環境管理器已經優於許多語言了，但每次都要重刻一次環境管理器類別，套用樣板，也太過麻煩，還好 Python 在其標準函式庫中提供了 `contextlib` 模組，裡面包含了許多有用東西能讓我們避免自己製作一個管理器類別，包含：

* `@contextmanager`
* `closing`
* `suppress`
* `redirect_stdout`
* `redirect_stderr`
* `ExitStack`
* `ContextDecorator`

> 有興趣的讀者可以看一下 [contextlib — Utilities for with-statement contexts][contextlib]

這邊我們只介紹一個被廣泛應用的裝飾器：`contextmanager`，他能夠裝飾一個僅含有 **單一yield** 的產生器函數使之成為一個環境管理器。

### 使用 generator 來實作環境管理器

我們來看看剛剛第二版的類別型管理器要如何使用 **產生器(generator)** 加上 `contextmanager` 來改寫：

首先產生器函數中會有一個 `yield`（這是產生器函數的定義），但只會有一個（這是 `contextmanager` 的要求）：

```python
import time
from contextlib import contextmanager # 從 contextlib 中匯入 contextmanager 裝飾器

@contextmanager
def clock():
    # 原本 __enter__ 做的事
    yield
    # 原本 __exit__ 做的事
```

接著我們把原本要放在 `__enter__` 中做的事情寫到 `yield` 前面：

```python
@contextmanager
def clock():
    print('start')
    t0 = time.time()
    yield
    # 原本 __exit__ 做的事
```

接著我們將 `__enter__` 要回傳的東西當作 `yield` 要產生的東西，原本我們回傳 `self`，不過這裡並沒有所謂的 `self`，而且其實 `clock` 並沒有在 `with` 中被使用到，所以，我們就純粹地寫一個 `yield`，讓他產生 `None` 就可以了。

最後讓我們將 `__exit__` 中要做的事情寫到 `yield` 後面：

```python
@contextmanager
def clock():
    print('start')
    t0 = time.time()
    yield
    print('stop')
    elapsed = time.time() - t0
    print('elapsed {}'.format(elapsed))
```

完成！是不是看起來簡潔多了！

而這樣的寫法在使用上也幾乎沒有什麼區別：

```python
with clock():
    time.sleep(3)
```

唯二的差別在於：

1. 原本環境管理器是類別實例化來的：`Clock()`，現在是使用產生器函數產生一個產生器：`clock()`。
2. 我們在 `with` 區塊內沒有要使用到 `clock()`，所以直接省去了 `with A as B` 中的 `as B`。

不過這樣的做法必須要注意一件事情，那就是用來當作環境管理器的產生器函數中只能有一個 `yield` 被執行。

> 詳細的原因也建議大家去讀 `contextmanager` 的代碼，我們在此就不多做討論，不過讀者們可以自己試試看能不能寫出 `contextmanager` 裝飾器，如果裝飾器的原理、產生器（協同程式）的原理和環境管理器的原理都已經明白的話，我們也能夠自己寫出！

接著我們來討論產生器函數形式的管理器如何處理例外，在類別型管理器中，Python 會自動捕捉例外並將之當成 `__exit__` 方法的參數，而我們可以在 `__exit__` 方法中做適當的處理，那產生器函數型的管理器該如何處理呢？

我們考慮以下的使用情境：

```python
with clock():
    1/0 # 此處將會引發例外
```

這個例外不但阻止了 `with` 區塊內其他代碼的執行，更使得 `__exit__` 方法的行為，也就是離開環境時要做的後處理被忽略了。這個例子的狀況倒是還好，就只是 `elapsed time` 沒有被印出，但如果是開關檔案的動作就會造成一定程度以上的危險，因為環境不會被切回來，檔案可能不會被關閉。

要處理這樣的例外，我們得讓 `yield` 出現在 `try/except` 結構中來捕捉例外，同時原本離開環境時要做的事情，也得放到 `finally` 區塊中：

```python
@contextmanager
def clock():
    # 進入環境時要做的動作
    print('start')
    t0 = time.time()
    
    # 處理例外
    try:
        yield
    except Exception as e:
        print(e)
        
    # 離開環境時要做的動作
    finally:
        print('stop')
        elapsed = time.time() - t0
        print('elapsed {}'.format(elapsed))
```

結果：

```python
start
division by zero
stop
elapsed 2.7894973754882812e-05
```

> 在 [Fluent Python][Fluent Python] 中，作者引用了 Leonardo Rochael 的註解，說明了使用 `contextmanager` 的代價：
>> 在 `yield` 外面包上 `try/finally`（或 `with` 區塊），是使用 `@contextmanager` 時必須付出的代價，因為你永遠不知道環境管理器的使用者會在他們的 `with` 區塊裡面做什麼。

### 巢狀的 with 述句

還記得前面我們使用了 `tag` 裝飾器和堆疊的手法在原函數的輸出前後印出指定的 html tag 頭尾：

```python
@tag('div')
@tag('p')
def content():
    print('content line')
    
content()
```

這裡我們也能夠用巢狀的 `with` 和環境管理器來做到：

```python
def content():
    print('content line')

@contextmanager
def tag(name):
    print('<{}>'.format(name))
    yield
    print('</{}>'.format(name))
    
with tag('div'):
    with tag('p'):
        content()
```

原因很簡單，這個任務的需求是在原本代碼執行的前後印出 tag 的頭跟尾。所以使用裝飾器做得到，因為我們能夠裝飾原函數，在其被呼叫的前後打印 tag 頭尾。使用環境管理器也做得到，因為我們能夠在 `with` 區塊被執行的前後打印 tag。

巢狀的 `with` 述句也可以寫成一行：

```python
with tag('div'), tag('p'):
    content()
```

順序是由左至右。這個手法其實相當實用，下次若要同時開啟很多檔案的時候，可以避免寫出階層式的巢狀：

```python
with open(f1, 'w') as writer:
    with open(f2, 'r') as reader:
        # read f2 and write to f1
```

改成使用平面式的巢狀：

```python
with open(f1, 'w') as writer, open(f2, 'r') as reader:
    # read f2 and write to f1
```

### 環境管理器小結

在這篇文章的後半部，我們認識了環境管理器的基本用法與寫法，包含了 `__enter__`、`__exit__` 和 `with`，也明白了 `as` 後面的東西就是 `__enter__` 的回傳值，`__exit__` 的參數和回傳值負責處理例外的發生。接著，我們用 `contextmanager` 搭配單一 `yield`的產生器函數簡便地實作環境管理器，同時說明了例外的處理方式，最後也了解到巢狀環境管理的使用。

## 結語

本篇文章從三明治的概念出發，一路介紹了裝飾器和環境管理器兩個非常具有 Python 特色的協定，我們除了分別掌握兩者的使用方法和時機之外，更要瞭解到，抽取外層（頭尾）作為復用的單元是一般副程式設計做不太到的事情，這個概念讓能讓我們的代碼更臻完美。

> 一定有朋友會問我說，講者在最後一部分點出的使用環境管理器作為裝飾器的部分在本文沒有被提及，但這個部分的複雜度更高，礙於篇幅，只好暫且擱置，不過這個概念的出發點，大家可以參考 `contextlib` 的 source code，其中的 `ContextDecorator` 中實作了 `__call__` 使得類別的實例成為了一個裝飾器，更重要的是，該裝飾器的核心動作便是以自身為環境管理器來啟動 `with` 區塊。

## 參考資料

* [PyConTw2017 Talk Slides: Don't Reinvent Sandwich - Python Decorator and Context Manager][Slides]
* [Fluent Python][Fluent Python]
* [PEP 343 -- The "with" Statement][PEP 343]
* [contextlib — Utilities for with-statement contexts][contextlib]

[Slides]:https://drive.google.com/file/d/0Bz8Kfu_94VuJcVo1a1drQjhReU0/view
[Speeker FB]:https://www.facebook.com/syhsiao0917?ref=ts&fref=ts
[Fluent Python]:http://shop.oreilly.com/product/0636920032519.do
[PEP 343]:https://www.python.org/dev/peps/pep-0343/
[contextlib]:https://docs.python.org/3.6/library/contextlib.html
