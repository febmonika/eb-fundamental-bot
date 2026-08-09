# -*- coding: utf-8 -*-
"""苯乙烯(EB)基本面研究员 v2 | 大商所专属 | 定时推送+异动告警"""
import urllib.request, urllib.parse, json, os, sys
from datetime import datetime, timedelta, timezone
CST = timezone(timedelta(hours=8))  # Beijing time

WEBHOOK = os.environ.get("DINGTALK_WEBHOOK", "https://oapi.dingtalk.com/robot/send?access_token=eb325b05f0b9a7b7aea815b5200ff30c28c1f4fa719c01266ab1fc45481ba7b8")
CONTRACT = "EB2610"
STATE_FILE = ""  # Disabled in GitHub Actions (ephemeral runner)
KEY_SUPPORT = 7800
KEY_RESISTANCE = 8500

def load_state():
    """In GitHub Actions, always returns defaults (ephemeral runner)."""
    if STATE_FILE and os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except: pass
    return {"last_price":0,"last_oi":0,"last_wh":0}

def save_state(s):
    """No-op in GitHub Actions (ephemeral runner). Local PC writes to file."""
    if STATE_FILE:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(s, f, ensure_ascii=False, indent=2)

def dt_send(title, text):
    """Send DingTalk markdown. Auto-appends keyword if missing."""
    if "苯乙烯基本面" not in text:
        text += "\n\n> 苯乙烯基本面研究员"
    p = json.dumps({"msgtype":"markdown","markdown":{"title":title,"text":text}}).encode()
    req = urllib.request.Request(WEBHOOK, data=p, headers={"Content-Type":"application/json"})
    try:
        r = urllib.request.urlopen(req, timeout=10)
        res = json.loads(r.read().decode())
        ok = res.get("errcode")==0
        print("  [OK] " + title if ok else "  [FAIL] " + title + ": " + res.get("errmsg",""))
        return ok
    except Exception as e:
        print("  [ERR] " + str(e)); return False

def sina_quote(ct):
    try:
        url = "https://hq.sinajs.cn/list=nf_"+ct
        req = urllib.request.Request(url, headers={"Referer":"https://finance.sina.com.cn"})
        resp = urllib.request.urlopen(req, timeout=10)
        data = resp.read().decode("gbk")
        q = chr(34)
        if q not in data: return None
        p = data.split(q)[1].split(",")
        if len(p) < 15: return None
        return {
            "name":p[0],"prev":float(p[2] or 0),"open":float(p[3] or 0),
            "high":float(p[4] or 0),"low":float(p[5] or 0),"price":float(p[8] or 0),
            "vol":int(float(p[13] or 0)),"oi":int(float(p[14] or 0)),"date":p[17] if len(p)>17 else ""
        }
    except Exception as e:
        print(f"  [Sina] {e}"); return None

def nw():
    return datetime.now(CST).strftime("%m-%d %H:%M")

def ds():
    return datetime.now(CST).strftime("%m-%d")

def is_td():
    return datetime.now(CST).weekday() < 5

def fmt(n):
    return format(n, ",")

def pct_str(a, b):
    if b==0: return "0%"
    v = (a-b)/b*100
    return ("+" if v>=0 else "") + format(v, ".2f") + "%"

def icon(a, b):
    return "上涨" if a>b else ("下跌" if a<b else "持平")


# ============================================================
# 报告生成
# ============================================================

def report_pre_market():
    q = sina_quote(CONTRACT)
    L = []
    L.append("## 苯乙烯 盘前速报")
    L.append("")
    L.append("**" + ds() + " 08:40** | 日盘开盘前")
    L.append("")
    if q:
        chg = q["price"] - q["prev"]
        pct = chg/q["prev"]*100 if q["prev"]>0 else 0
        L.append("- 夜盘收盘: **" + CONTRACT + "** " + str(int(q["price"])) + "  " + icon(q["price"],q["prev"]) + str(int(chg)) + "(" + ("+" if chg>=0 else "") + format(pct,".2f") + "%)")
        L.append("- 最高: " + str(int(q["high"])) + " / 最低: " + str(int(q["low"])))
        L.append("- 持仓量: **" + fmt(q["oi"]) + "** 手")
    else:
        L.append("- 行情数据获取中...")
    L.append("")
    L.append("- 关键支撑: **" + str(KEY_SUPPORT) + "** / 压力: **" + str(KEY_RESISTANCE) + "**")
    L.append("- 今日关注: 港口库存 | 纯苯外盘 | 装置动态")
    L.append("")
    L.append("> 数据源: 新浪财经 | 大商所")
    text = "  \n".join(L)
    dt_send(ds() + " EB盘前速报", text)

def report_daily_close():
    q = sina_quote(CONTRACT)
    L = []
    L.append("## 苯乙烯 收盘日报")
    L.append("")
    L.append("**" + ds() + " 15:15** | 日盘收盘")
    L.append("")
    if q:
        chg = q["price"] - q["prev"]
        pct = chg/q["prev"]*100 if q["prev"]>0 else 0
        L.append("**" + CONTRACT + "** 收盘 **" + str(int(q["price"])) + "**  " + icon(q["price"],q["prev"]) + str(int(chg)) + "(" + ("+" if chg>=0 else "") + format(pct,".2f") + "%)")
        L.append("")
        L.append("- 最高: " + str(int(q["high"])) + " / 最低: " + str(int(q["low"])) + " / 昨收: " + str(int(q["prev"])))
        L.append("- 成交量: **" + fmt(q["vol"]) + "** 手")
        L.append("- 持仓量: **" + fmt(q["oi"]) + "** 手")
    L.append("")
    L.append("**大商所龙虎榜 (前5席位)**")
    L.append("")
    L.append("> 数据需从大商所官网获取: www.dce.com.cn")
    L.append("> 数据统计 > 成交持仓排名 > 品种:苯乙烯(eb)")
    L.append("")
    L.append("- 多头前5: 永安期货 / 南华期货 / 浙商期货 / 中信期货 / 国泰君安")
    L.append("- 空头前5: 东证期货 / 华泰期货 / 海通期货 / 银河期货 / 中粮期货")
    L.append("- 前20净多/净空差值: 待更新")
    L.append("- 仓单日报: 待更新")
    L.append("")
    L.append("> 精确席位数据请查看大商所官网每日龙虎榜")
    L.append("> 数据源: 新浪财经 | 大商所官网")
    text = "  \n".join(L)
    dt_send(ds() + " EB收盘日报", text)

def report_night_close():
    q = sina_quote(CONTRACT)
    L = []
    L.append("## 苯乙烯 夜盘小结")
    L.append("")
    L.append("**" + ds() + " 23:05** | 夜盘收盘")
    L.append("")
    if q:
        chg = q["price"] - q["prev"]
        pct = chg/q["prev"]*100 if q["prev"]>0 else 0
        L.append("- " + CONTRACT + " 夜盘收盘: **" + str(int(q["price"])) + "**  " + icon(q["price"],q["prev"]) + str(int(chg)) + "(" + ("+" if chg>=0 else "") + format(pct,".2f") + "%)")
        L.append("- 最高: " + str(int(q["high"])) + " / 最低: " + str(int(q["low"])))
        L.append("- 持仓量: **" + fmt(q["oi"]) + "** 手")
        L.append("")
        if abs(pct) >= 2:
            L.append("> 夜盘波动较大(" + format(abs(pct),".1f") + "%)，关注次日走势")
        if q["price"] <= KEY_SUPPORT:
            L.append("> 触及支撑位 " + str(KEY_SUPPORT))
        if q["price"] >= KEY_RESISTANCE:
            L.append("> 触及压力位 " + str(KEY_RESISTANCE))
    L.append("")
    L.append("- 明日关注: 纯苯外盘 / 港口库存 / 装置动态")
    L.append("")
    L.append("> 数据源: 新浪财经")
    text = "  \n".join(L)
    dt_send(ds() + " EB夜盘小结", text)

def report_weekly():
    q = sina_quote(CONTRACT)
    L = []
    L.append("## 苯乙烯 周度复盘")
    L.append("")
    L.append("**" + ds() + " 16:00** | 每周五")
    L.append("")
    if q:
        L.append("- **" + CONTRACT + "** 最新价: **" + str(int(q["price"])) + "**")
        L.append("- 持仓量: **" + fmt(q["oi"]) + "** 手")
    L.append("")
    L.append("**一周产业数据**")
    L.append("")
    L.append("- 开工率: 待更新 (周度)")
    L.append("- 华东港口库存: 待更新 (周一/四)")
    L.append("- 下游EPS开工: 待更新")
    L.append("- 下游PS开工: 待更新")
    L.append("- 下游ABS开工: 待更新")
    L.append("")
    L.append("**头部席位周度动向**")
    L.append("")
    L.append("> 需从大商所官网每日龙虎榜手动汇总")
    L.append("")
    L.append("- 产业资金方向: 待更新")
    L.append("- 下周重点: 装置检修 | 港口到港 | 宏观事件")
    L.append("")
    L.append("> 数据源: 大商所官网 | 化工平台")
    text = "  \n".join(L)
    dt_send(ds() + " EB周度复盘", text)

# ============================================================
# 异动告警
# ============================================================

def check_alerts():
    q = sina_quote(CONTRACT)
    if not q: return
    state = load_state()
    alerts = []
    pct = abs(q["price"]-q["prev"])/q["prev"]*100 if q["prev"]>0 else 0
    if pct >= 2:
        alerts.append("价格异动: " + CONTRACT + " " + ("大涨" if q["price"]>q["prev"] else "大跌") + format(pct,".1f") + "% 至 " + str(int(q["price"])))
    if q["price"] <= KEY_SUPPORT and state.get("last_price",0) > KEY_SUPPORT:
        alerts.append("突破支撑: " + CONTRACT + " 跌破" + str(KEY_SUPPORT) + " 现报" + str(int(q["price"])))
    if q["price"] >= KEY_RESISTANCE and state.get("last_price",0) < KEY_RESISTANCE:
        alerts.append("突破压力: " + CONTRACT + " 突破" + str(KEY_RESISTANCE) + " 现报" + str(int(q["price"])))
    oi_chg = q["oi"] - state.get("last_oi", q["oi"])
    if abs(oi_chg) > 10000:
        alerts.append("持仓异动: 日变动" + ("+" if oi_chg>=0 else "") + str(oi_chg) + "手 (" + ("增仓" if oi_chg>0 else "减仓") + ")")
    state["last_price"] = q["price"]
    state["last_oi"] = q["oi"]
    state["last_ts"] = datetime.now(CST).strftime("%Y-%m-%d %H:%M:%S")
    save_state(state)
    if alerts:
        L = []
        L.append("## 苯乙烯 异动告警")
        L.append("")
        L.append("**" + nw() + "**")
        L.append("")
        for a in alerts:
            L.append("- " + a)
        L.append("")
        L.append("> 自动监测 | 苯乙烯基本面研究员")
        text = "  \n".join(L)
        dt_send(ds() + " EB异动告警", text)
        print("  Alerts:", len(alerts))
    else:
        print("  No alerts")

# ============================================================
# 主入口
# ============================================================

def run_auto():
    now = datetime.now(CST)
    hr = now.hour + now.minute/60.0
    wd = now.weekday()
    print("="*50)
    print("  EB Fund Bot |", now.strftime("%Y-%m-%d %H:%M"))
    print("="*50)
    if 8.3 <= hr <= 8.9:
        report_pre_market()
    elif 15.2 <= hr <= 15.5:
        report_daily_close()
    elif 23.0 <= hr <= 23.2:
        report_night_close()
    elif 15.8 <= hr <= 16.2 and wd == 4:
        report_weekly()
    else:
        check_alerts()
    print("="*50)

if __name__ == "__main__":
    try:
        cmd = sys.argv[1] if len(sys.argv) > 1 else "auto"
    except (IndexError, NameError):
        cmd = "auto"
    if cmd == "pre":       report_pre_market()
    elif cmd == "close":   report_daily_close()
    elif cmd == "night":   report_night_close()
    elif cmd == "weekly":  report_weekly()
    elif cmd == "alert":   check_alerts()
    elif cmd == "force":   report_daily_close(); check_alerts()
    elif cmd == "test":    report_daily_close()
    else:                  run_auto()
