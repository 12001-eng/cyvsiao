"""
辦公室工作職掌數據導入腳本
將前台靜態數據導入到後台管理系統中

運行方式：
python import_office_data.py
"""

import os
import sys
from app import app, db
from models import OfficeResponsibility, OfficeWorkDetail, OfficeSchedule

# 職位層級定義
OFFICE_POSITIONS = [
    {"title": "處室主任", "name": "主任", "order": 0},
    {"title": "僑生組組長", "name": "組長", "order": 1},
    {"title": "建教組組長", "name": "組長", "order": 1},
    {"title": "僑生組", "name": "幹事", "order": 2},
    {"title": "建教組", "name": "幹事", "order": 2},
]

# 詳細工作職掌數據 - 按職位分類
WORK_DETAILS_DATA = {
    "director": [
        {
            "title": "一、核心策略與計畫統籌",
            "position_type": "director",
            "content": """<h4>核心策略與計畫統籌</h4>
<ul>
<li><strong>年度計畫總召集</strong>：統籌擬定及修訂「產學攜手合作計畫」與「僑生專班實施計畫」，確認符合教育部國教署與僑委會之規範。</li>
<li><strong>預算編列與控管</strong>：審核實習處年度預算，包含實習材料費、僑生補助款、招生經費及設備更新經費之配置。</li>
<li><strong>科大端對接 (關鍵)</strong>：與合作的科技大學（+4端）系主任或院長保持密切聯繫，確認課程銜接、轉段名額及升學門檻，確保「7年一貫」暢通。</li>
<li><strong>召開委員會</strong>：擔任「建教合作委員會」及「僑生輔導委員會」之執行秘書或召集人，主持重大議案討論。</li>
<li><strong>處室整體業務運作規劃</strong>：針對僑生組與建教組之業務，進行階段性及臨時任務的調整與分派，以維持處室人力資源的運作與業務順利推行。</li>
</ul>""",
            "order": 0
        },
        {
            "title": "二、廠商開發與公共關係",
            "position_type": "director",
            "content": """<h4>廠商開發與公共關係</h4>
<ul>
<li><strong>優質廠商決策</strong>：親自視察潛在合作廠商，進行最終篩選決策（決定跟誰簽約），確保廠商具備培訓能力且形象良好。</li>
<li><strong>外部資源爭取</strong>：爭取產業界捐贈設備、提供獎助學金，或引進業師協同教學。</li>
<li><strong>官方應對</strong>：負責接待教育部、僑委會、勞動局之視導與評鑑，並針對缺失進行改善回覆。</li>
<li><strong>危機公關發言</strong>：若發生學生重大工安意外或負面新聞，協助校長擬定對外發言策略，並與廠商高層協調賠償與善後機制。</li>
</ul>""",
            "order": 1
        },
        {
            "title": "三、內部管理與督導",
            "position_type": "director",
            "content": """<h4>內部管理與督導</h4>
<ul>
<li><strong>跨組協調</strong>：解決建教組（管實習）與僑生組（管生活）之間的灰色地帶衝突（例如：學生因護照過期無法進廠，責任歸屬與後續處理）。</li>
<li><strong>績效考核</strong>：督導並考核組長（建教、僑生、巡廠老師）及校內導師之工作績效。</li>
</ul>""",
            "order": 2
        },
        {
            "title": "四、學生權益與風險控管",
            "position_type": "director",
            "content": """<h4>學生權益與風險控管</h4>
<ul>
<li><strong>工安與法規紅線</strong>：嚴格監督建教組落實「不超時、不輪大夜班、津貼不低於法規」的三不原則，避免學校被處以高額罰款或停招。</li>
<li><strong>緊急事件指揮</strong>：擔任學生重大傷病、職場性騷擾、罷工或集體適應不良事件的緊急應變小組指揮官。</li>
<li><strong>休退學控管</strong>：定期檢視僑生流失率，針對高風險學生召開個案會議，盡力降低退學率（影響下年度核班）。</li>
</ul>""",
            "order": 3
        }
    ],
    "overseas": [
        {
            "title": "一、招生與入境作業",
            "position_type": "overseas_lead",
            "content": """<h4>招生與入境作業</h4>
<ul>
<li><strong>招生宣傳與錄取作業</strong>
  <ul>
  <li>協助編印招生簡章及宣傳資料。</li>
  <li>辦理僑生申請入學資格審查。</li>
  <li>寄發錄取通知及入學相關文件。</li>
  </ul>
</li>
<li><strong>新生入境與報到</strong>
  <ul>
  <li>辦理簽證（Visa）及入境相關手續。</li>
  <li>安排接機服務與入校交通。</li>
  <li>辦理新生註冊、住宿安排與環境介紹。</li>
  <li>舉辦新生始業輔導（視基礎訓練而定）。</li>
  </ul>
</li>
</ul>""",
            "order": 0
        },
        {
            "title": "二、證件與法規管理",
            "position_type": "overseas_staff",
            "content": """<h4>證件與法規管理</h4>
<ul>
<li><strong>居留證（ARC）管理</strong>
  <ul>
  <li>協助辦理初次辦證、延期、異動登記。</li>
  <li>畢業後留台（覓職期）居留證申請輔導。</li>
  </ul>
</li>
<li><strong>工作許可證（Work Permit）</strong>
  <ul>
  <li><strong>(核心業務)</strong> 協助學生申請及展延工作許可證。</li>
  <li>控管工讀時數符合勞動部法規（學期間每週 20 小時限制）。</li>
  </ul>
</li>
</ul>""",
            "order": 1
        },
        {
            "title": "三、生活輔導與照顧",
            "position_type": "overseas_staff",
            "content": """<h4>生活輔導與照顧</h4>
<ul>
<li><strong>醫療與保險</strong>
  <ul>
  <li>辦理僑生健康保險（僑保）及全民健保（健保）加退保。</li>
  <li>協助學生就醫及保險理賠申請。</li>
  </ul>
</li>
<li><strong>生活適應與諮詢</strong>
  <ul>
  <li>建立僑生通訊錄與緊急聯絡網。</li>
  <li>定期訪視宿舍，關懷生活起居與衛生習慣。</li>
  <li>提供心理諮詢轉介（針對思鄉、課業壓力等）。</li>
  </ul>
</li>
</ul>""",
            "order": 2
        },
    ],
    "coop": [
        {
            "title": "一、計畫與行政",
            "position_type": "coop_lead",
            "content": """<h4>計畫與行政</h4>
<ul>
<li>擬定建教合作年度實施計畫與預算編列。</li>
<li>撰寫與陳報建教合作班之申請、評估與審核文件（對接國教署）。</li>
<li>督導組內業務執行進度與績效考核。</li>
<li>召開建教合作委員會及相關協調會議。</li>
<li>辦理建教生基礎訓練及職前訓練業務。</li>
</ul>""",
            "order": 0
        },
        {
            "title": "二、廠商開發與評估",
            "position_type": "coop_staff",
            "content": """<h4>廠商開發與評估</h4>
<ul>
<li>開發優質合作廠商，進行初步篩選與洽談。</li>
<li>辦理廠商評估作業（確認工作環境、安全性、訓練內容）。</li>
<li>代表學校與合作廠商簽訂「建教合作契約」。</li>
</ul>""",
            "order": 1
        },
        {
            "title": "三、學生管理與權益",
            "position_type": "coop_staff",
            "content": """<h4>學生管理與權益</h4>
<ul>
<li>處理建教生重大勞資爭議或職場性騷擾/霸凌事件。</li>
<li>統籌建教生之基礎訓練與職前訓練規劃。</li>
<li>規劃教師駐廠輔導及巡迴輔導訪視行程。</li>
<li>審核建教生之輪調分配與轉廠/退廠機制。</li>
</ul>""",
            "order": 2
        },
    ]
}

# 年度工作時程
SCHEDULE_DATA = [
    {
        "category": "overseas",
        "time_range": "1月 - 2月",
        "task": "<ul><li>海外招生後續追蹤</li><li>寒假休轉學生招收與輔導</li><li>春節祭祖聯歡餐會籌辦</li></ul>",
        "order": 0
    },
    {
        "category": "coop",
        "time_range": "1月 - 3月",
        "task": "<ul><li>確認本年度合作廠商</li><li>爭取與協調春節祭祖餐會活動之經費贊助</li></ul>",
        "order": 0
    },
    {
        "category": "overseas",
        "time_range": "4月 - 6月",
        "task": "<ul><li>核定新生錄取名單</li><li>辦理學生入境簽證文件與宿舍整備</li><li>提報開班計畫</li><li>協助建教組進行評估</li></ul>",
        "order": 1
    },
    {
        "category": "coop",
        "time_range": "2月 - 4月",
        "task": "<ul><li>陳報下學年度建教班開班計畫</li><li>進行廠商開發、篩選與評估</li></ul>",
        "order": 1
    },
    {
        "category": "overseas",
        "time_range": "7月 - 8月",
        "task": "<ul><li>安排機場接機服務</li><li>居留證與工作許可申請 (最急件辦理)</li><li>新生宿舍與生活起居餐點安排</li></ul>",
        "order": 2
    },
    {
        "category": "coop",
        "time_range": "5月 - 6月",
        "task": "<ul><li>召開建教合作委員會以確認合作機構</li></ul>",
        "order": 2
    },
    {
        "category": "coop",
        "time_range": "7月 - 8月",
        "task": "<ul><li>辦理建教生基礎訓練與職前訓練 (基礎訓練216小時)</li><li>簽訂三方訓練契約</li></ul>",
        "order": 3
    },
    {
        "category": "overseas",
        "time_range": "9月 - 1月",
        "task": "<ul><li>安排工讀及廠區實習協調</li><li>定期訪視與生活輔導</li><li>每月出勤及工作許可追蹤</li></ul>",
        "order": 4
    },
    {
        "category": "coop",
        "time_range": "9月 - 1月",
        "task": "<ul><li>分發進廠實習、每月或每兩週進行訪視輔導</li><li>處理生活津貼查核</li><li>定期職場訪視，填寫訪視紀錄表</li></ul>",
        "order": 4
    },
]

def clear_existing_data():
    """清除現有的工作職掌相關數據"""
    print("清除現有數據...")
    OfficeWorkDetail.query.delete()
    OfficeSchedule.query.delete()
    # 保留 OfficeResponsibility 以保持職位信息
    db.session.commit()
    print("✓ 清除完成")

def import_work_details():
    """導入詳細工作職掌"""
    print("\n導入詳細工作職掌...")
    count = 0
    for category, items in WORK_DETAILS_DATA.items():
        for item in items:
            detail = OfficeWorkDetail(
                category=category,
                title=item["title"],
                content=item["content"],
                order=item.get("order", 0)
            )
            db.session.add(detail)
            count += 1
    db.session.commit()
    print(f"✓ 導入 {count} 條工作職掌")

def import_schedules():
    """導入年度工作時程"""
    print("\n導入年度工作時程...")
    for item in SCHEDULE_DATA:
        schedule = OfficeSchedule(
            category=item["category"],
            time_range=item["time_range"],
            task=item["task"],
            order=item.get("order", 0)
        )
        db.session.add(schedule)
    db.session.commit()
    print(f"✓ 導入 {len(SCHEDULE_DATA)} 條年度時程")

def main():
    """主函數"""
    with app.app_context():
        print("=" * 50)
        print("啟英國際處 工作職掌數據導入")
        print("=" * 50)
        
        # 清除舊數據
        clear_existing_data()
        
        # 導入新數據
        import_work_details()
        import_schedules()
        
        print("\n" + "=" * 50)
        print("✓ 所有數據導入完成！")
        print("=" * 50)

if __name__ == "__main__":
    main()
