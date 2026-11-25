取证包移交到第三方之后，中间两条证据被换掉，校验仍然说整包完好：每条证据必须带序号与前一条的摘要；序号必须连续且从一开始；任何一条被替换或删除都要能定位到序号；整包摘要由全部条目决定；移交要记录双方与时间；同一证据不得出现在两个包里；批量校验各包独立。不变量：链完整时校验通过；任意单条修改都会失败并给出序号。

契约说明：

一条链是条目列表，每个条目包含 seq、prev、entry、hash 四个键。entry 是证据内容，至少包含 id 与 payload。prev 保存前一条的摘要，链首的 prev 是固定的零摘要。hash 是条目自身的摘要。

entry_hash(prev, entry) 计算条目摘要，结果同时取决于前一条摘要与条目序号。

append(chain, entry) 返回追加后的新链，序号从一开始连续递增。

verify(chain) 校验整条链，返回包含 ok 与 first_bad 的映射。链完整时 ok 为真，first_bad 为空；否则 ok 为假，first_bad 是首个断点的序号。

package_digest(chain) 返回整包摘要，链中任意条目变化都会改变该值。

handover(chain, from_party, to_party, now) 返回移交记录，包含移交双方、移交时间与整包摘要。

duplicate_check(packages, entry_id) 返回包含指定证据的包名列表。

validate_chain(chain) 返回问题描述列表，覆盖缺少序号、序号重复与摘要长度错误。

evidence_batch(packages) 逐包校验，返回包名到校验结果的映射，各包互不影响。

## 字段表

| 字段 | 取值 |
| --- | --- |
| 所属领域 | 安全 |
| 子方向 | 漏洞检测与攻防 |
| 任务类型 | Bugfix |
| 语言/框架 | Python 3, pytest |
| 环境可复现等级 | 无外部依赖 |

