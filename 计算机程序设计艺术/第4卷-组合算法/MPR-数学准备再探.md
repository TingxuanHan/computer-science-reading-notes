# 【计算机程序设计艺术 TAOCP】卷4·MPR 数学准备再探：从条件期望到鞅与概率尾界

> 阅读定位：本篇依据资料包中的《第4卷 第5册A Mathematical Preliminaries Redux》预稿，页脚日期为2015年10月3日。讲解正文为书内第1—12页，对应PDF第7—18页；习题从书页第12页延续至第25页。原文用 **MPR** 引用这部分，它是第四卷的数学补充，没有7.3或8.1这样的节号。本文保留这一标记，中文题名“数学准备再探”为本文译法。
>
> 本篇以独立编写的例子和Python程序说明主要方法；预稿与后来正式版本的页码、内容可能不同，查阅时以这里给出的文件和页码为准。

@[TOC]

## 一、为什么读到组合算法，还要回来补概率

枚举程序可以逐个产生对象，回溯程序会剪掉不可能成功的分支。但在分析这些程序时，另一些问题会出现：随机输入下要访问多少节点？某次运行比平均值慢很多的概率有多大？若依次观察随机选择，能否不断修正对最终成本的预测？

这些问题需要的工具不同。知道平均成本，并不能直接知道极端成本的概率；知道两个随机量各自的分布，也不能直接把它们的概率相乘。

MPR把这些分析工具集中在一起。本文先建立条件期望的含义，再讨论概率界，最后把它们接到同一个随机分配模型上。

## 二、先写明随机性在哪里

考虑把$n$个有编号的球，独立、均匀地投入$m$个有编号的桶。一个完整结果是

$$
\omega=(x_1,\ldots,x_n),\qquad x_i\in\{0,\ldots,m-1\}.
$$

这里共有$m^n$个等可能结果，每个概率为$m^{-n}$。设$Q$为最后的空桶数量，它是完整结果的函数。

事件是结果集合。例如，“至少两个桶为空”就是满足$Q(\omega)\ge2$的所有结果。随机变量则为每个结果赋值，例如$Q(\omega)$。

若事件$B$的概率为正，条件概率为

$$
\Pr(A\mid B)=\frac{\Pr(A\cap B)}{\Pr(B)}.
$$

它把样本空间缩到$B$，再把概率重新归一化。本文只在条件事件有正概率时使用这个商；离散模型中，零概率条件不会参与后面的加权和。

### 两两独立不够保证联合独立

取两个独立公平比特$U,V$，再令$W=U\mathbin{\oplus}V$。三个比特的可能结果只有

```text
(U,V,W) = (0,0,0), (0,1,1), (1,0,1), (1,1,0)
```

任意两个比特的四种组合都等可能，因此它们两两独立；但

$$
\Pr(U=1,V=1,W=1)=0\ne\frac18.
$$

所以三个比特不联合独立。写下概率乘积之前，必须确认所需的是哪一级独立性。程序里复用随机种子或用少量随机位派生多个变量时，这一点尤其容易被忽略。

## 三、条件期望是一份随信息更新的预测

对于离散随机变量，期望是按概率加权的平均值：

$$
\mathbb E X=\sum_x x\Pr(X=x).
$$

令$I_j$表示“第$j$个桶最终为空”的指示变量，即为空时取1，否则取0。于是

$$
Q=\sum_{j=0}^{m-1}I_j,
\qquad
\mathbb E Q=\sum_{j=0}^{m-1}\mathbb E I_j
=m\left(1-\frac1m\right)^n.
$$

每个桶为空的概率，是所有球都避开它的概率。这里用到了球的独立性，但**期望求和本身不要求各个$I_j$独立**。实际上，一个桶是否为空会与其他桶的状态相关。

### “给定一个值”与“给定一个随机变量”

$\mathbb E[X\mid Y=y]$是已知$Y=y$后的平均值。把$y$换成实际观察到的随机结果$Y$，便得到新的随机变量$\mathbb E[X\mid Y]$。它会随观察结果变化。

先在每个$Y=y$的分组内求平均，再把各组按概率加起来，就回到原来的总体平均：

$$
\mathbb E X=\sum_y\mathbb E[X\mid Y=y]\Pr(Y=y)
=\mathbb E\bigl[\mathbb E[X\mid Y]\bigr].
$$

这就是全期望公式。它依赖分组加权，不依赖$X$和$Y$独立。

回到空桶模型。观察了前$i$个球的去向后，设当前还有$e_i$个桶为空。已经非空的桶不可能再变空；每个当前空桶还需要躲过剩下的$n-i$个球。因此

$$
Z_i=\mathbb E[Q\mid X_1,\ldots,X_i]
=e_i\left(1-\frac1m\right)^{n-i}.
$$

在开始时，$Z_0=\mathbb E Q$；全部去向揭晓后，$Z_n=Q$。中间各项是同一个最终结果在不同信息下的预测，而不是不同实验的平均值。

## 四、从平均值走向概率：先选对不等式

### 1. Markov：把坏事件换成非负代价

对非负随机变量$X$和$a>0$，逐个结果都有

$$
X\ge a\,\mathbf1_{\{X\ge a\}}.
$$

两边取期望，得到

$$
\Pr(X\ge a)\le\frac{\mathbb E X}{a}.
$$

Markov界的条件很少，因此也可能很松。若右边大于1，只能把它截到1；这并不表示事件概率真的超过1。

更一般地，可以为坏事件设计一个非负函数$f(X)$：坏事一发生，$f(X)$至少为$a$。随后对$f(X)$应用同一思路。许多尾界正是从这里得到的。

### 2. Chebyshev：度量偏离平均值的平方

记$\mu=\mathbb E X$。把Markov用于$(X-\mu)^2$，便有

$$
\Pr(|X-\mu|\ge t)
\le\frac{\operatorname{Var}(X)}{t^2},\qquad t>0.
$$

这要求方差有限。它限制的是偏差，而不是$X$本身。求和变量的方差时还要保留协方差项：

$$
\operatorname{Var}\left(\sum_i X_i\right)
=\sum_i\operatorname{Var}(X_i)
+2\sum_{i<j}\operatorname{Cov}(X_i,X_j).
$$

不能因为用了期望线性性，就顺手把方差也线性拆开。

### 3. Jensen：先变换还是先平均

若$f$在随机变量取值的区间上为凸函数，相关期望存在，则

$$
f(\mathbb E X)\le\mathbb E f(X).
$$

例如对$f(x)=x^2$，有$(\mathbb E X)^2\le\mathbb E[X^2]$；对正随机变量和$f(x)=1/x$，有$1/\mathbb E X\le\mathbb E[1/X]$。随机成本取倒数以后再求平均，一般不等于平均成本的倒数。

### 4. 一阶矩和二阶矩：能否保证至少存在一个

若非负整数$X$表示满足条件的对象数量，那么$X>0$时至少为1，所以

$$
\Pr(X>0)\le\mathbb E X.
$$

反过来，若$\mathbb E[X^2]$有限且为正，可以用Cauchy–Schwarz：

$$
\mathbb E X
=\mathbb E[X\mathbf1_{\{X>0\}}]
\le\sqrt{\mathbb E[X^2]\Pr(X>0)}.
$$

于是得到二阶矩下界

$$
\Pr(X>0)\ge\frac{(\mathbb E X)^2}{\mathbb E[X^2]}.
$$

这条下界也适用于一般非负随机变量。若$X$恒为0，应直接得到概率0，不去计算$0/0$。

为什么只知道“平均有一个”不够？若$X$以$1/M$的概率取$M$，其他时候为0，则$\mathbb E X=1$，但$\Pr(X>0)=1/M$。二阶矩为$M$，正好揭示了这种由罕见大值抬高平均数的情况。

### 5. 指示变量之和还能利用条件信息

原文第5页介绍了Ross的条件期望下界。设$X=\sum_j I_j$，其中$I_j$取0或1，记$p_j=\Pr(I_j=1)$，则

$$
\Pr(X>0)\ge\sum_{j:p_j>0}
\frac{p_j}{\mathbb E[X\mid I_j=1]}.
$$

理解它可以从一个恒等式出发：当$X>0$时，各个$I_j/X$相加恰好为1；当$X=0$时，把这些项定义为0。因此

$$
\Pr(X>0)=\sum_{j:p_j>0}p_j\,
\mathbb E[1/X\mid I_j=1].
$$

再在每个条件分布内对$1/x$使用Jensen，即得到上面的界。它并不要求指示变量相互独立；需要能算出或控制条件均值。

MPR还把相关性问题引向习题中的FKG不等式。例如，在独立Bernoulli坐标组成的乘积分布下，两个递增事件满足$\Pr(A\cap B)\ge\Pr(A)\Pr(B)$。这里“递增”指把一些坐标从0改成1，不会让已成立的事件失效。这个结论依赖分布和单调性条件，不能扩展成“任意两个事件都正相关”。

## 五、鞅：下一次预测的条件平均，等于现在的预测

在有限模型中，可以把$\mathcal F_i$理解为“前$i$步已知的全部信息”。若$Z_i$可由这些信息决定、可积，并且

$$
\mathbb E[Z_{i+1}\mid\mathcal F_i]=Z_i,
$$

就称它为相对于这些信息的鞅。它允许很强的依赖关系，也不要求每条路径保持不变。

空桶预测$Z_i$正是一个例子。当前有$e_i$个空桶，下一球落进空桶的概率为$e_i/m$，于是

$$
\mathbb E[e_{i+1}\mid\mathcal F_i]
=e_i-\frac{e_i}{m}.
$$

代入预测公式：

$$
\mathbb E[Z_{i+1}\mid\mathcal F_i]
=\left(e_i-\frac{e_i}{m}\right)
\left(1-\frac1m\right)^{n-i-1}=Z_i.
$$

更一般地，逐步揭示随机输入，并定义$Z_i=\mathbb E[Q\mid\mathcal F_i]$，就得到Doob鞅。这来自条件期望的塔式法则。

### Pólya球罐：比例稳定，路径仍会分化

原文用Pólya球罐说明另一种鞅。罐里有$r$个红球和$b$个黑球，每次随机抽出一个球，放回后再加入一个同色球。下次红球比例的条件期望为

$$
\frac r{r+b}\frac{r+1}{r+b+1}
+\frac b{r+b}\frac r{r+b+1}
=\frac r{r+b}.
$$

所以红球比例是鞅。这个结论说的是条件平均，不意味着红黑数量会沿每条路径越来越接近，也不意味着每次抽球相互独立。

### 停止规则必须说明条件

若停止时刻$T$只由已观察的信息决定，并且有固定上界$T\le N$，那么对可积鞅有

$$
\mathbb E Z_T=\mathbb E Z_0.
$$

在这个有界情形下可以直接解释。令$D_i=Z_i-Z_{i-1}$，则

$$
Z_T=Z_0+\sum_{i=1}^{N}\mathbf1_{\{T\ge i\}}D_i.
$$

是否继续第$i$步，在看到第$i$步结果前已经决定；而$D_i$给定过去的条件期望为0，所以每项的期望都为0。无界停止不能直接套用这一证明，需要额外条件。

## 六、从鞅得到尾界：控制每次揭示的信息影响

对于鞅差分$D_i$，若存在确定的界$a_i\le D_i\le b_i$，且$\mathbb E[D_i\mid\mathcal F_{i-1}]=0$，则Hoeffding–Azuma界给出

$$
\Pr\left(\left|\sum_{i=1}^{n}D_i\right|\ge t\right)
\le2\exp\left(-\frac{2t^2}{\sum_{i=1}^{n}(b_i-a_i)^2}\right).
$$

若只知道$|D_i|\le c_i$，应取区间宽度$2c_i$，于是指数变成$-t^2/(2\sum_i c_i^2)$。区间宽度和绝对值上界相差一倍，不能混用常数。

### 有界差分法怎样用于空桶

设$Q=f(X_1,\ldots,X_n)$，各个$X_i$独立。如果只改变第$i$个输入、其他输入保持不变，函数值的变化不超过$c_i$，则有

$$
\Pr(|Q-\mathbb E Q|\ge t)
\le2\exp\left(-\frac{2t^2}{\sum_i c_i^2}\right).
$$

这是由Doob鞅得到的有界差分界。独立输入保证：固定已揭示的前缀后，比较第$i$个输入的不同取值时，可以对同一个未来输入分布取平均。因此该步条件预测的取值区间宽度至多$c_i$。它比把差分粗略夹在$[-c_i,c_i]$里能保留更多信息。

在空桶模型中，把一个球从桶$a$改放到桶$b$：原桶可能多出一个空桶，目标桶可能少一个空桶，这两个变化的符号相反，总变化只可能是$-1,0,1$。所以每个$c_i=1$，得到

$$
\Pr\left(\left|Q-m\left(1-\frac1m\right)^n\right|\ge t\right)
\le\min\left\{1,2e^{-2t^2/n}\right\},\qquad n\ge1.
$$

这里没有假装各个空桶指示变量独立。独立的是每个球的去向，$Q$本身可以是它们的复杂函数。

原文还用装箱问题说明：一个目标函数即使难以精确求值，仍可能证明它集中在均值附近。集中性保证本身不会给出均值的具体值，也不会自动提供一个高效的最优解算法。

### 最后一步没超界，途中是否超界是另一件事

MPR还讨论了最大值不等式。若$Z_i$是非负下鞅，即条件均值至少为当前值，则对$a>0$有

$$
\Pr\left(\max_{0\le i\le n}Z_i\ge a\right)
\le\frac{\mathbb E Z_n}{a}.
$$

这约束整段运行中是否曾经越过阈值，和只检查最后一刻不同。分析一个随机过程的峰值时，应先确认需要控制的究竟是哪一个事件。

## 七、用精确穷举检查一个小实例

以下程序使用Python标准库，取4个球和4个桶，枚举全部$4^4=256$种结果。`Fraction`保留精确有理数，避免浮点误差掩盖等式问题。

程序检查三件事：两两独立不推出联合独立；空桶的一阶矩、二阶矩和存在概率；每个前缀下，下一步预测的平均确实等于当前预测。

```python
from collections import Counter
from fractions import Fraction as F
from itertools import combinations, product


triples = [(u, v, u ^ v) for u, v in product(range(2), repeat=2)]
for i, j in combinations(range(3), 2):
    counts = Counter((row[i], row[j]) for row in triples)
    assert set(counts.values()) == {1} and len(counts) == 4
assert (1, 1, 1) not in triples

m, n = 4, 4
outcomes = list(product(range(m), repeat=n))
empty = [m - len(set(row)) for row in outcomes]
total = len(outcomes)
mean = F(sum(empty), total)
second = F(sum(q * q for q in empty), total)
positive = F(sum(q > 0 for q in empty), total)
assert mean == m * F(m - 1, m) ** n
assert mean * mean / second <= positive <= min(F(1), mean)

# Q^2 = sum(I_j) + sum_{j != k}(I_j I_k).
second_formula = mean + m * (m - 1) * F(m - 2, m) ** n
assert second == second_formula


def prediction(prefix):
    e = m - len(set(prefix))
    return e * F(m - 1, m) ** (n - len(prefix))


checked = 0
for i in range(n):
    for prefix in product(range(m), repeat=i):
        next_average = sum(
            (prediction(prefix + (b,)) for b in range(m)), F(0)
        ) / m
        assert next_average == prediction(prefix)
        checked += 1

assert all(prediction(row) == q for row, q in zip(outcomes, empty))
print("distribution:", sorted(Counter(empty).items()))
print("E[Q] =", mean, "E[Q^2] =", second)
print("P(Q > 0) =", positive)
print("second-moment lower bound =", mean * mean / second)
print("martingale prefixes checked =", checked)
```

输出为：

```text
distribution: [(0, 24), (1, 144), (2, 84), (3, 4)]
E[Q] = 81/64 E[Q^2] = 129/64
P(Q > 0) = 29/32
second-moment lower bound = 2187/2752
martingale prefixes checked = 85
```

例如，实际存在空桶的概率为$29/32$，二阶矩法给出的下界为$2187/2752$。两者并不相等：下界可以用于保证，不能当成精确概率。

由于两个指定桶同时为空的概率为$((m-2)/m)^n$，程序中的二阶矩公式可以独立推得：

$$
\mathbb E[Q^2]
=m\left(1-\frac1m\right)^n
+m(m-1)\left(1-\frac2m\right)^n,\qquad m\ge2.
$$

这里第二项来自有序桶对，不是只计一次的无序桶对，所以系数是$m(m-1)$。

穷举适合核对这个小实例。一般$n$下，$m^n$个结果很快就枚举不动；这正是前面的推导和概率界发挥作用的地方。有限检查也不能替代不等式的一般性证明。

## 八、渐近概率很小，还要问随规模怎样变小

MPR末尾区分了两种强度。第一种是失败概率趋于0，即成功事件$A_n$满足

$$
\Pr(A_n)\longrightarrow1.
$$

该预稿在这个渐近语境下使用a.s.记号。阅读其他概率论材料时，要核对定义，不能把这里的写法直接替换成随机变量序列“以概率1收敛”的另一种断言。

更强的q.s.要求失败概率比任意固定的逆多项式都小：对每个固定$K>0$，

$$
\Pr(\overline{A_n})=O(n^{-K}).
$$

例如$e^{-cn}$（$c>0$固定）满足这个条件；$n^{-10}$虽然趋于0，却不满足“对每个$K$”的要求。

这种强度在要同时保证很多事件时很有用。如果有至多$n^d$个事件，而且它们的失败概率具有统一的上述界，取$K>d$并用并集界就能控制“至少一个失败”的概率：

$$
\Pr\left(\bigcup_j\overline{A_{n,j}}\right)
\le\sum_j\Pr(\overline{A_{n,j}})
\le C_K n^{d-K}.
$$

要让合并后的事件仍然q.s.，对任意目标幂次$L$再取$K>d+L$即可。这里不要求事件彼此独立，但需要对这批事件统一有效的概率上界。

渐近结论还应和具体规模分开。一个指数上界在$n$很小时仍可能大于1；这时只能说它没有给出有用的数值保证，不能靠“指数衰减”四个字跳过计算。

## 九、回到原文时怎样读

| 原稿书页 | 本篇对应内容 | 读时要保留的条件 |
|---|---|---|
| 1—3（PDF 7—9） | 概率空间、独立性、条件期望 | 条件事件概率；求和和乘积的不同要求 |
| 4—5（PDF 10—11） | Markov、Chebyshev、Jensen、矩方法 | 非负性、可积性、凸性、二阶矩分母 |
| 6—8（PDF 12—14） | 鞅、Pólya球罐、停止规则 | 相对于哪些信息；停止时刻是否有界 |
| 9—11（PDF 15—17） | 最大值界、尾界、Doob鞅、有界差分 | 区间宽度；输入独立性；单坐标变化幅度 |
| 11—12（PDF 17—18） | 渐近事件和q.s. | 失败概率的衰减速度及统一性 |

把这些方法接到算法上时，可以先写出三行：**随机输入是什么，最终成本是什么，当前已知信息是什么。** 然后再决定是求期望、估计存在概率，还是限制偏离均值及运行峰值。这样每个公式都有明确的问题与假设，不会只剩下一个熟悉的不等式名称。

---

**参考来源**：Donald E. Knuth, *The Art of Computer Programming*, Volume 4, Pre-Fascicle 5A, *Mathematical Preliminaries Redux*，用户提供资料包内的2015年10月3日预稿，书页1—12，相关习题见12—25页。本文按该文件组织阅读定位，未将预稿页码当作正式版页码。
