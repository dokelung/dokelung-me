Title: Don't Reinvent Sandwich 2: Context Manager
Date: 2017-06-25 22:05
Category: python
Tags: python, 
Slug: dont-reinvent-sandwich-2

<div class="uk-thumbnail uk-thumbnail-medium">
    <img src="{attach}images/slides_cover.png" alt="slides_cover.png">
</div>

今年的 Pycon Taiwan，有一篇我滿感興趣的演講：Don't Reinvent Sandwich - Python Decorator and Context Manager，講者是蕭聖穎先生。

> 該演講的 [投影片][Slides] 和講者的 [Facebook][Speeker FB]。

由於我對於語言本身的設計和使用慣例非常感興趣，所以就去朝聖了一下。講題的主旨大略是：我們通常透過抽取一段重複出現的 **連續代碼** 成為 **函數 (function)** 或 **類別 (class)** 來重複利用他，避免重複發明輪子。但有的時候想要抽取的部分並非 **中間** (
三明治的餡）連續的部分，而是 **頭尾** （三明治的麵包），這個時候我們便需要使用一些其他的手法或機制來達到 reuse 的目的了。Python 正好非常友善地提供了 **裝飾器 (decorator)** 和 **環境管理器 (context manager)**，可以很容易地達成我們的目的。

這場演講給出了非常有意思的想法，尤其是裝飾器與環境管理器的互通。但很可惜的是，雖然 Python 的 decorator 和 context manager 非常有自己的特色也是許多大型專案常用的技術，但是對於初學者而言還是一個相對進階的主題，我認為初學者並不容易在這短短的四十五分鐘內了解全部的內容，所以寫了這篇文章，希望能詳細地頗析本場演講所涵蓋到的內容，期待能對大家有所幫助，不過所學慎淺，班門弄斧不免貽笑大方，那就還請講者及各路高手海涵。

本文的脈絡大致會依循講者的投影片，內容的部分也是，會有適度的補充，就容我多撈叨一兩句，而較零碎的細節就容我略過不提了。

> 另外，本文的許多例子和想法都來自 [Fluent Python][Fluent Python] 這本書，這是我迄今看過最好的 Python 書籍了。

由於本文相當長，為了閱讀上的方便我將它分成前後兩篇，分別著重在 Python 的裝飾器和環境管理器，這是本文的下半部分，我們會討論 Python 的環境管理器。

* 延伸閱讀：[Don't Reinvent Sandwich: Decorator](http://dokelung.me/category/python/dont-reinvent-sandwich)

---

## 環境管理器

接著我們進入另一個主題：**環境管理器(context manager)** 或又稱 **情境管理器**。

環境管理器是一個能夠撘配 `with` 述句使用的類別，他能夠在切入環境時進行 **環境的設定** 和若干 **預處理** 的行為，並且能夠在離開環境時進行 **重置** 並做 **善後處理**（包含處理例外的發生）。

我們在 [PEP 343 -- The "with" Statement][PEP 343] 中，可以了解到 `with` 和 環境管理器的基本概念，同時裡面有點出了一個重要的概念就是：

> with statement makes it possible to factor out standard uses of try/finally statements

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
    time.sleep(3)
except Exception as e: # 發生例外，捕捉並當成參數傳入 __exit__
    if not clock.__exit__(type(e), e, e.__traceback__)
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