# -*- coding: utf-8 -*-
"""
海关编码智能查询系统 - HS编码数据初始化
数据来源：WCO国际海关组织 + 中国海关总署
Version: 1.0.0
"""

import sqlite3
import json
import os
import sys

# 确保能找到models模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from models import get_db_context

# ============================================================
# WCO HS 2022 国际通用编码（前2位）- 21大类
# 数据来源：世界海关组织(WCO) https://www.wcoomd.org
# ============================================================

WCO_HS_CHAPTERS = [
    ("01", 2, "活动物", "Live animals"),
    ("02", 2, "肉及食用杂碎", "Meat and edible meat offal"),
    ("03", 2, "鱼、甲壳动物等", "Fish and crustaceans, molluscs and other aquatic invertebrates"),
    ("04", 2, "乳品;蛋品;天然蜂蜜", "Dairy produce; birds' eggs; natural honey"),
    ("05", 2, "其他动物产品", "Products of animal origin, not elsewhere specified"),
    ("06", 2, "活树及其他活植物", "Live trees and other plants; bulbs, roots and the like"),
    ("07", 2, "食用蔬菜、根及块茎", "Edible vegetables and certain roots and tubers"),
    ("08", 2, "食用水果及坚果", "Edible fruit and nuts; peel of citrus fruit or melons"),
    ("09", 2, "咖啡、茶、马黛茶及香料", "Coffee, tea, maté and spices"),
    ("10", 2, "谷物", "Cereals"),
    ("11", 2, "制粉工业产品", "Products of the milling industry"),
    ("12", 2, "含油子仁及果实", "Oil seeds and oleaginous fruits; miscellaneous grains"),
    ("13", 2, "虫胶;树胶、树脂", "Lac; gums, resins and other vegetable saps and extracts"),
    ("14", 2, "编结用植物材料", "Vegetable plaiting materials; vegetable products not elsewhere specified"),
    ("15", 2, "动、植物油、脂", "Animal or vegetable fats and oils and their cleavage products"),
    ("16", 2, "肉、鱼、甲壳动物的制品", "Preparations of meat, of fish or of crustaceans"),
    ("17", 2, "糖及糖食", "Sugars and sugar confectionery"),
    ("18", 2, "可可及可可制品", "Cocoa and cocoa preparations"),
    ("19", 2, "谷物、粉、乳的制品", "Preparations of cereals, flour, starch or milk"),
    ("20", 2, "蔬菜、水果、坚果的制品", "Preparations of vegetables, fruit, nuts or other parts of plants"),
    ("21", 2, "杂项食品", "Miscellaneous edible preparations"),
    ("22", 2, "饮料、酒及醋", "Beverages, spirits and vinegar"),
    ("23", 2, "食品工业的残渣及废料", "Residues and waste from the food industries"),
    ("24", 2, "烟草及烟草代用品", "Tobacco and manufactured tobacco substitutes"),
    ("25", 2, "盐;硫磺;泥土及石料", "Salt; sulphur; earths and stone; plastering materials"),
    ("26", 2, "矿砂、矿渣及矿灰", "Ores, slag and ash"),
    ("27", 2, "矿物燃料、矿物油", "Mineral fuels, mineral oils and products of their distillation"),
    ("28", 2, "无机化学品", "Inorganic chemicals; organic or inorganic compounds of precious metals"),
    ("29", 2, "有机化学品", "Organic chemicals"),
    ("30", 2, "药品", "Pharmaceutical products"),
    ("31", 2, "肥料", "Fertilisers"),
    ("32", 2, "鞣料浸膏及染料浸膏", "Tanning or dyeing extracts; tannins and their derivatives"),
    ("33", 2, "精油及香膏", "Essential oils and resinoids; perfumery, cosmetic or toilet preparations"),
    ("34", 2, "肥皂、有机表面活性剂", "Soap, organic surface-active agents, washing preparations"),
    ("35", 2, "蛋白类物质;改性淀粉", "Albuminoidal substances; modified starches; glues; enzymes"),
    ("36", 2, "炸药;烟火制品", "Explosives; pyrotechnic products; matches; pyrophoric alloys"),
    ("37", 2, "照相及电影用品", "Photographic or cinematographic goods"),
    ("38", 2, "化学品", "Chemical products not elsewhere specified or included"),
    ("39", 2, "塑料及其制品", "Plastics and articles thereof"),
    ("40", 2, "橡胶及其制品", "Rubber and articles thereof"),
    ("41", 2, "生皮（毛皮除外）及皮革", "Raw hides and skins (other than furskins) and leather"),
    ("42", 2, "皮革制品;鞍具及挽具", "Articles of leather; saddlery and harness; travel goods"),
    ("43", 2, "毛皮、人造毛皮及其制品", "Furskins and artificial fur; manufactures thereof"),
    ("44", 2, "木及木制品;木炭", "Wood and articles of wood; wood charcoal"),
    ("45", 2, "软木及软木制品", "Cork and articles of cork"),
    ("46", 2, "稻草、秸秆、编结材料制品", "Manufactures of straw, of esparto or of other plaiting materials"),
    ("47", 2, "木浆;纤维状纤维素浆", "Pulp of wood or of other fibrous cellulosic material"),
    ("48", 2, "纸及纸板;纸浆、纸制品", "Paper and paperboard; articles of paper pulp"),
    ("49", 2, "书籍、报纸、印刷品", "Printed books, newspapers, pictures and other products"),
    ("50", 2, "蚕丝", "Silk"),
    ("51", 2, "羊毛、动物细毛或粗毛", "Wool, fine or coarse animal hair; horsehair yarn and woven fabric"),
    ("52", 2, "棉花", "Cotton"),
    ("53", 2, "其他植物纺织纤维", "Vegetable textile fibres not elsewhere specified"),
    ("54", 2, "化学纤维长丝", "Man-made filaments"),
    ("55", 2, "化学纤维短纤", "Man-made staple fibres"),
    ("56", 2, "絮胎、毡呢及无纺织物", "Wadding, felt and nonwovens; special yarns"),
    ("57", 2, "地毯及纺织材料的其他铺地制品", "Carpets and other textile floor coverings"),
    ("58", 2, "特种织物;簇绒织物", "Special woven fabrics; tufted textile fabrics; lace"),
    ("59", 2, "浸渍、涂布、包覆的纺织物", "Impregnated, coated, covered or laminated textile fabrics"),
    ("60", 2, "针织物及钩编织物", "Knitted or crocheted fabrics"),
    ("61", 2, "针织或钩编的服装及衣着附件", "Articles of apparel and clothing accessories, knitted or crocheted"),
    ("62", 2, "非针织或非钩编的服装及衣着附件", "Articles of apparel and clothing accessories, not knitted or crocheted"),
    ("63", 2, "其他纺织制成品", "Other made up textile articles; sets; worn clothing and rags"),
    ("64", 2, "鞋靴、护腿和类似品", "Footwear, gaiters and the like; parts of such articles"),
    ("65", 2, "帽类及其零件", "Headgear and parts thereof"),
    ("66", 2, "雨伞、阳伞、手杖", "Umbrellas, sun umbrellas, walking sticks, seat-sticks, whips"),
    ("67", 2, "已加工羽毛、羽绒及其制品", "Prepared feathers and down and articles made of feathers or of down"),
    ("68", 2, "石料、石膏、水泥、石棉", "Articles of stone, plaster, cement, asbestos, mica or similar materials"),
    ("69", 2, "陶瓷产品", "Ceramic products"),
    ("70", 2, "玻璃及其制品", "Glass and glassware"),
    ("71", 2, "天然或养殖珍珠、宝石或半宝石", "Natural or cultured pearls, precious or semi-precious stones"),
    ("72", 2, "钢铁", "Iron and steel"),
    ("73", 2, "钢铁制品", "Articles of iron or steel"),
    ("74", 2, "铜及其制品", "Copper and articles thereof"),
    ("75", 2, "镍及其制品", "Nickel and articles thereof"),
    ("76", 2, "铝及其制品", "Aluminium and articles thereof"),
    ("78", 2, "铅及其制品", "Lead and articles thereof"),
    ("79", 2, "锌及其制品", "Zinc and articles thereof"),
    ("80", 2, "锡及其制品", "Tin and articles thereof"),
    ("81", 2, "其他贱金属、金属陶瓷", "Other base metals; cermets; articles thereof"),
    ("82", 2, "贱金属工具、器具、利口器", "Tools, implements, cutlery, spoons and forks, of base metal"),
    ("83", 2, "贱金属杂项制品", "Miscellaneous articles of base metal"),
    ("84", 2, "核反应堆、锅炉、机器、机械器具", "Nuclear reactors, boilers, machinery and mechanical appliances"),
    ("85", 2, "电机、电气设备及其零件", "Electrical machinery and equipment and parts thereof"),
    ("86", 2, "铁道及电车道机车等", "Railway or tramway locomotives, rolling-stock and parts thereof"),
    ("87", 2, "车辆及其零件、附件", "Vehicles other than railway or tramway rolling-stock"),
    ("88", 2, "航空器、航天器及其零件", "Aircraft, spacecraft, and parts thereof"),
    ("89", 2, "船舶及浮动结构体", "Ships, boats and floating structures"),
    ("90", 2, "光学、照相、电影、计量、检验、精密仪器", "Optical, photographic, cinematographic, measuring, checking, precision instruments"),
    ("91", 2, "钟表及其零件", "Clocks and watches and parts thereof"),
    ("92", 2, "乐器及其零件、附件", "Musical instruments; parts and accessories of such articles"),
    ("93", 2, "武器、弹药及其零件、附件", "Arms and ammunition; parts and accessories thereof"),
    ("94", 2, "家具;寝具、褥垫、弹簧床垫", "Furniture; bedding, mattresses, mattress supports, cushions"),
    ("95", 2, "玩具、游戏品、运动用品", "Toys, games and sports requisites; parts and accessories thereof"),
    ("96", 2, "杂项制品", "Miscellaneous manufactured articles"),
    ("97", 2, "艺术品、收藏品及古物", "Works of art, collectors' pieces and antiques"),
    ("98", 2, "特殊商品（如军事物资等）", "Special classification provisions"),
]

# ============================================================
# 常用HS编码4位和6位详细数据（高频查询）
# 数据来源：中国海关总署 + WCO
# 格式: (编码, 层级, 中文描述, 英文描述, 单位, 关税, 增值税, 退税率, 监管条件, 搜索关键词)
# ============================================================

COMMON_HS_CODES = [
    # === 电子电气类 ===
    ("8471", 4, "自动数据处理设备及其部件", "Automatic data processing machines and units thereof", "台", 0, 13, 13, "A", "电脑,笔记本,计算机,服务器,主机,平板电脑,laptop,computer,server"),
    ("847130", 6, "便携式自动数据处理设备，重量≤10kg", "Portable digital ADP machines, ≤10kg", "台", 0, 13, 13, "A", "笔记本电脑,便携电脑,laptop,notebook"),
    ("847141", 6, "其他自动数据处理设备", "Other ADP machines, comprising in the same housing at least a CPU and an I/O unit", "台", 0, 13, 13, "A", "台式电脑,一体机,desktop,all-in-one"),
    ("847149", 6, "其他自动数据处理系统", "Other ADP machines, presented in the form of systems", "台", 0, 13, 13, "A", "工作站,服务器,workstation"),
    ("847150", 6, "自动数据处理设备的部件", "ADP units, magnetic or optical readers", "台", 0, 13, 13, "A", "电脑配件,硬盘,光驱,computer parts"),
    ("847170", 6, "存储部件", "Storage units", "台", 0, 13, 13, "A", "硬盘,固态硬盘,U盘,SSD,HDD,USB drive"),
    ("8517", 4, "电话机（含蜂窝网络电话）", "Telephone sets, including smartphones", "台", 0, 13, 13, "A", "手机,电话,智能手机,phone,mobile,smartphone,cellphone"),
    ("851713", 6, "智能手机", "Smartphones", "台", 0, 13, 13, "A", "智能手机,手机,iphone,android phone,smartphone"),
    ("851712", 6, "其他电话机", "Other telephone sets", "台", 0, 13, 13, "A", "座机,固定电话,电话机,landline telephone"),
    ("851762", 6, "接收、转换和发送或再生声音、图像或其他数据的设备", "Machines for the reception, conversion and transmission or regeneration of voice, images or other data", "台", 0, 13, 13, "A", "路由器,交换机,网络设备,router,switch,network equipment"),
    ("851770", 6, "电话机及其他设备的零件", "Parts of telephone sets and other equipment", "千克", 0, 13, 13, "A", "手机配件,电话配件,phone parts"),
    ("8518", 4, "传声器（麦克风）及其零件;扬声器", "Microphones and stands therefor; loudspeakers", "个", 0, 13, 13, "A", "麦克风,扬声器,音响,喇叭,microphone,speaker"),
    ("851821", 6, "单喇叭音箱", "Single loudspeaker, mounted in enclosure", "个", 0, 13, 13, "A", "音箱,蓝牙音箱,speaker,bluetooth speaker"),
    ("851829", 6, "多喇叭音箱", "Multiple loudspeaker, mounted in enclosure", "个", 0, 13, 13, "A", "音响系统,家庭影院,sound system"),
    ("851830", 6, "耳机", "Headphones", "个", 0, 13, 13, "A", "耳机,耳塞,headphone,earphone,earbuds"),
    ("8523", 4, "光盘、磁带、固态非易失性存储器件等", "Discs, tapes, solid-state non-volatile storage devices", "个", 0, 13, 13, "A", "存储卡,SD卡,TF卡,memory card,SD card"),
    ("852351", 6, "固态非易失性存储器件（如闪存卡）", "Solid-state non-volatile storage devices", "个", 0, 13, 13, "A", "闪存卡,存储卡,memory card,flash storage"),
    ("852589", 6, "其他激光器", "Other lasers", "台", 0, 13, 13, "A", "激光器,laser,激光设备"),
    ("8525", 4, "无线电广播、电视发送设备;摄像机", "Transmission apparatus for radio-telephony, television, cameras", "台", 0, 13, 13, "A", "摄像头,摄像机,监控摄像头,camera,webcam"),
    ("852510", 6, "无线电话发送设备", "Transmission apparatus for radio-telephony", "台", 0, 13, 13, "A", "基站,信号发射器,base station"),
    ("852581", 6, "雷达设备", "Radar apparatus", "台", 0, 13, 13, "A", "雷达,雷达设备,radar"),
    ("8528", 4, "电视接收装置（含监视器、投影机）", "Television receivers (including monitors and projectors)", "台", 0, 13, 13, "A", "电视,显示器,监视器,投影仪,TV,monitor,projector"),
    ("852872", 6, "彩色电视接收装置", "Color television receivers", "台", 0, 13, 13, "A", "彩色电视,液晶电视,LED电视,color TV,LCD TV"),
    ("852862", 6, "其他监视器", "Other monitors", "台", 0, 13, 13, "A", "电脑显示器,显示器,computer monitor"),
    ("853400", 6, "印刷电路板", "Printed circuits", "千克", 0, 13, 13, "A", "电路板,PCB,印刷电路板,printed circuit board"),
    ("8541", 4, "二极管、晶体管及类似的半导体器件", "Diodes, transistors and similar semi-conductor devices", "个", 0, 13, 13, "A", "二极管,晶体管,半导体,芯片,diode,transistor,semiconductor,chip"),
    ("854110", 6, "发光二极管(LED)", "Light-emitting diodes (LED)", "个", 0, 13, 13, "A", "LED,发光二极管,LED灯珠"),
    ("854121", 6, "耗散功率小于1W的晶体管", "Transistors with dissipation rate < 1W", "个", 0, 13, 13, "A", "晶体管,三极管,transistor"),
    ("854140", 6, "太阳能电池", "Solar cells", "个", 0, 13, 13, "A", "太阳能电池,光伏电池,solar cell,solar panel"),
    ("8542", 4, "电子集成电路", "Electronic integrated circuits", "个", 0, 13, 13, "A", "集成电路,IC,芯片,integrated circuit,microchip"),
    ("854231", 6, "处理器及控制器", "Processors and controllers", "个", 0, 13, 13, "A", "CPU,GPU,处理器,微处理器,processor"),
    ("854232", 6, "存储器", "Memories", "个", 0, 13, 13, "A", "内存,存储器,RAM,ROM,memory"),
    ("854233", 6, "放大器", "Amplifiers", "个", 0, 13, 13, "A", "放大器,运放,amplifier"),
    ("854239", 6, "其他集成电路", "Other electronic integrated circuits", "个", 0, 13, 13, "A", "集成电路,芯片,IC,integrated circuit"),
    ("8544", 4, "绝缘电线、电缆", "Insulated wire, cable", "千克", 0, 13, 13, "A", "电线,电缆,数据线,充电线,wire,cable,USB cable"),
    ("8504", 4, "变压器、静止式变流器", "Electrical transformers, static converters", "个", 0, 13, 13, "A", "变压器,电源适配器,充电器,transformer,power adapter,charger"),
    ("850440", 6, "静止式变流器", "Static converters", "个", 0, 13, 13, "A", "电源适配器,充电器,开关电源,power adapter,charger"),
    ("8507", 4, "蓄电池", "Electric accumulators", "个", 0, 13, 13, "A", "电池,蓄电池,锂电池,battery,lithium battery"),
    ("850760", 6, "锂离子蓄电池", "Lithium-ion accumulators", "个", 0, 13, 13, "A", "锂电池,锂离子电池,lithium-ion battery"),
    ("8508", 4, "电动机械", "Electro-mechanical tools", "台", 0, 13, 13, "A", "电动工具,电钻,电锯,power tool,electric drill"),
    ("8509", 4, "家用电动器具", "Electro-mechanical domestic appliances", "台", 0, 13, 13, "A", "家用电器,电风扇,搅拌机,home appliance"),
    ("8516", 4, "电热水器、电热器具", "Electric space heating, hair dryers", "台", 0, 13, 13, "A", "电热水器,吹风机,电暖器,heater,hair dryer"),
    ("8511", 4, "电气照明装置", "Electrical lighting equipment", "个", 0, 13, 13, "A", "灯具,LED灯,照明,lighting,LED lamp"),

    # === 机械类 ===
    ("8481", 4, "阀门及类似装置", "Valves and similar appliances", "个", 0, 13, 13, "A", "阀门,水阀,球阀,valve,ball valve"),
    ("8482", 4, "滚动轴承", "Rolling bearings", "个", 0, 13, 13, "A", "轴承,滚珠轴承,滚动轴承,bearing,ball bearing"),
    ("8483", 4, "传动轴、齿轮箱等", "Transmission shafts, gears, gearing", "个", 0, 13, 13, "A", "齿轮,传动轴,变速箱,gear,transmission"),
    ("8486", 4, "半导体制造设备", "Machine tools for working semiconductor materials", "台", 0, 13, 13, "A", "半导体设备,芯片制造设备,semiconductor equipment"),
    ("8456", 4, "用激光等处理材料的机床", "Machine tools for working any material by removal of material, operated by laser", "台", 0, 13, 13, "A", "激光切割机,激光雕刻机,laser cutting machine"),
    ("8457", 4, "加工中心", "Machine tool centres", "台", 0, 13, 13, "A", "加工中心,数控机床,CNC,machining center"),
    ("8458", 4, "车床", "Lathes for removing metal", "台", 0, 13, 13, "A", "车床,lathe"),
    ("8459", 4, "铣床", "Milling machines", "台", 0, 13, 13, "A", "铣床,milling machine"),
    ("8460", 4, "磨床", "Grinding or polishing machines", "台", 0, 13, 13, "A", "磨床,研磨机,grinding machine"),
    ("8462", 4, "压力机", "Machine tools for working metal by forging", "台", 0, 13, 13, "A", "压力机,冲床,press machine"),
    ("8467", 4, "手提式电动工具", "Hand-held tools with self-contained electric motor", "台", 0, 13, 13, "A", "手电钻,电动扳手,electric drill,impact wrench"),
    ("8479", 4, "其他未列名的机器及机械器具", "Machines and mechanical appliances having individual functions", "台", 0, 13, 13, "A", "包装机,灌装机,分拣机,packaging machine"),
    ("8421", 4, "过滤、净化装置", "Filtering or purifying machinery and apparatus", "台", 0, 13, 13, "A", "过滤器,净水器,空气净化器,filter,purifier"),
    ("8423", 4, "衡器（称量仪器）", "Weighing machinery", "台", 0, 13, 13, "A", "秤,电子秤,天平,weighing scale,balance"),
    ("8425", 4, "起重机、提升机", "Hoists, lifts and cranes", "台", 0, 13, 13, "A", "起重机,吊车,电梯,升降机,crane,elevator,hoist"),
    ("8427", 4, "叉车", "Fork-lift trucks", "台", 0, 13, 13, "A", "叉车,forklift"),
    ("8428", 4, "输送机、升降机", "Lifting, handling, loading or unloading machinery", "台", 0, 13, 13, "A", "输送带,传送带,升降台,conveyor,belt conveyor"),
    ("8429", 4, "推土机、挖掘机等", "Self-propelled bulldozers, excavators", "台", 0, 13, 13, "A", "挖掘机,推土机,装载机,excavator,bulldozer,loader"),
    ("8433", 4, "收割机、割草机", "Harvesting or threshing machinery", "台", 0, 13, 13, "A", "收割机,割草机,harvester,lawn mower"),
    ("8443", 4, "印刷机械", "Printing machinery", "台", 0, 13, 13, "A", "打印机,复印机,印刷机,printer,photocopier,printing press"),
    ("844332", 6, "打印机", "Printers, copying machines, facsimile machines", "台", 0, 13, 13, "A", "打印机,复印机,传真机,printer,photocopier,fax"),
    ("8414", 4, "风扇、通风机", "Air or vacuum pumps, fans", "台", 0, 13, 13, "A", "风扇,风机,通风机,真空泵,fan,blower,vacuum pump"),
    ("8415", 4, "空气调节器", "Air conditioning machines", "台", 0, 13, 13, "A", "空调,air conditioner"),
    ("8418", 4, "冷藏箱、冷冻箱等", "Refrigerators, freezers and other refrigerating equipment", "台", 0, 13, 13, "A", "冰箱,冰柜,冷柜,冷藏柜,refrigerator,freezer"),
    ("8419", 4, "加热、冷却设备", "Machinery for treatment of materials by a process involving change of temperature", "台", 0, 13, 13, "A", "工业烤箱,烘干机,加热器,industrial oven,dryer"),

    # === 车辆运输 ===
    ("8703", 4, "小客车（含轿车、越野车）", "Motor cars and other motor vehicles", "辆", 15, 13, 13, "4AB", "汽车,轿车,越野车,SUV,car,automobile"),
    ("870323", 6, "汽油型小客车，排量1000ml-1500ml", "Motor cars with spark-ignition engine, 1000cc-1500cc", "辆", 15, 13, 13, "4AB", "小排量汽车,1.2L汽车,1.5L汽车"),
    ("870324", 6, "汽油型小客车，排量1500ml-3000ml", "Motor cars with spark-ignition engine, 1500cc-3000cc", "辆", 15, 13, 13, "4AB", "2.0L汽车,2.5L汽车,中型轿车"),
    ("8704", 4, "货车", "Motor vehicles for the transport of goods", "辆", 0, 13, 13, "A", "卡车,货车,皮卡,truck,pickup"),
    ("8705", 4, "特种车辆", "Special purpose motor vehicles", "辆", 0, 13, 13, "A", "消防车,救护车,工程车,special vehicle"),
    ("8708", 4, "汽车零件及附件", "Parts and accessories of motor vehicles", "千克", 0, 13, 13, "A", "汽车配件,汽车零件,auto parts,car parts"),
    ("870899", 6, "其他汽车零件及附件", "Other parts and accessories of motor vehicles", "千克", 0, 13, 13, "A", "汽车配件,汽车零件,auto parts"),
    ("8711", 4, "摩托车", "Motorcycles", "辆", 0, 13, 13, "A", "摩托车,电动车,motorcycle"),
    ("8712", 4, "自行车", "Bicycles and other cycles", "辆", 0, 13, 13, "A", "自行车,电动车,bicycle,e-bike"),
    ("8802", 4, "其他航空器", "Other aircraft (e.g. helicopters, airplanes)", "架", 0, 13, 13, "A", "飞机,直升机,aircraft,helicopter,airplane"),
    ("8803", 4, "航空器零件", "Parts of aircraft", "千克", 0, 13, 13, "A", "飞机零件,航空配件,aircraft parts"),
    ("8601", 4, "铁路机车", "Railway locomotives", "辆", 0, 13, 13, "A", "火车,机车,火车头,locomotive"),
    ("8903", 4, "货船", "Cargo ships", "艘", 0, 13, 13, "A", "货船,集装箱船,cargo ship,container ship"),

    # === 纺织服装 ===
    ("6109", 4, "T恤衫、汗衫", "T-shirts, singlets and other vests, knitted or crocheted", "件", 0, 13, 13, "A", "T恤,T恤衫,t-shirt"),
    ("6110", 4, "针织套头衫、开襟衫", "Jerseys, pullovers, cardigans, waistcoats, knitted", "件", 0, 13, 13, "A", "毛衣,针织衫,卫衣,sweater,pullover,hoodie"),
    ("6203", 4, "男式西服套装、便服套装", "Men's or boys' suits, ensembles, jackets, trousers", "件", 0, 13, 13, "A", "男装,西装,西裤,men's suit,trousers"),
    ("6204", 4, "女式西服套装、连衣裙", "Women's or girls' suits, ensembles, jackets, dresses", "件", 0, 13, 13, "A", "女装,连衣裙,裙子,women's dress,skirt"),
    ("6205", 4, "男衬衫", "Men's or boys' shirts", "件", 0, 13, 13, "A", "男衬衫,衬衫,shirt"),
    ("6206", 4, "女衬衫", "Women's or girls' blouses, shirts", "件", 0, 13, 13, "A", "女衬衫,衬衫,blouse"),
    ("6212", 4, "胸衣、束腰带等", "Brassieres, corsets, girdles, suspenders", "件", 0, 13, 13, "A", "内衣,胸衣,文胸,underwear,brassiere"),
    ("6302", 4, "床上用品", "Bed linen, table linen, toilet linen and kitchen linen", "千克", 0, 13, 13, "A", "床单,被套,枕套,床上用品,bedding,bed sheet"),
    ("6304", 4, "装饰用品", "Bedspreads, quilts, eiderdowns", "千克", 0, 13, 13, "A", "窗帘,靠垫,装饰织物,curtain,cushion"),
    ("5806", 4, "狭幅织物", "Narrow woven fabrics", "千克", 0, 13, 13, "A", "织带,松紧带,拉链,ribbon,elastic band,zipper"),
    ("6403", 4, "皮革制鞋靴", "Footwear with outer soles of leather", "双", 0, 13, 13, "A", "皮鞋,leather shoes"),
    ("6404", 4, "纺织材料制鞋靴", "Footwear with outer soles of rubber, plastics, leather", "双", 0, 13, 13, "A", "运动鞋,帆布鞋,sports shoes,sneakers"),
    ("4202", 4, "箱包", "Trunks, suitcases, briefcases, school satchels", "个", 0, 13, 13, "A", "箱包,行李箱,手提包,背包,luggage,suitcase,backpack,bag"),
    ("420310", 6, "皮革制衣箱", "Trunks, suitcases of leather", "个", 0, 13, 13, "A", "行李箱,皮箱,luggage,leather suitcase"),
    ("420221", 6, "皮革制手提包", "Handbags with outer surface of leather", "个", 0, 13, 13, "A", "皮包,手提包,leather bag,handbag"),
    ("420222", 6, "塑料制手提包", "Handbags with outer surface of plastics", "个", 0, 13, 13, "A", "塑料包,手提包,plastic bag,handbag"),
    ("420229", 6, "纺织材料制手提包", "Handbags with outer surface of textile materials", "个", 0, 13, 13, "A", "帆布包,布包,canvas bag"),
    ("420292", 6, "塑料制箱包", "Trunks, suitcases of plastics", "个", 0, 13, 13, "A", "塑料箱,塑料行李箱,plastic suitcase"),
    ("420231", 6, "纺织材料制背包", "Other bags with outer surface of textile materials", "个", 0, 13, 13, "A", "帆布背包,双肩包,canvas backpack"),
    ("420291", 6, "皮革制背包", "Other bags with outer surface of leather", "个", 0, 13, 13, "A", "皮背包,双肩包,leather backpack"),
    ("420232", 6, "塑料制背包", "Other bags with outer surface of plastics", "个", 0, 13, 13, "A", "塑料背包,双肩包,plastic backpack"),

    # === 塑料橡胶 ===
    ("3917", 4, "塑料管子及其附件", "Tubes, pipes and hoses of plastics", "千克", 0, 13, 13, "A", "塑料管,PVC管,塑料管材,plastic pipe,PVC pipe"),
    ("3919", 4, "胶粘板、片、膜等", "Self-adhesive plates, sheets, film of plastics", "千克", 0, 13, 13, "A", "胶带,不干胶,贴膜,adhesive tape,adhesive film"),
    ("3920", 4, "塑料板、片、膜、箔", "Plates, sheets, film, foil, strip of plastics", "千克", 0, 13, 13, "A", "塑料板,塑料膜,亚克力板,塑料片,plastic sheet,acrylic"),
    ("3923", 4, "塑料制盒、箱、容器", "Boxes, cases, crates of plastics", "千克", 0, 13, 13, "A", "塑料盒,塑料箱,塑料容器,plastic box,plastic container"),
    ("3924", 4, "塑料制餐具、厨房用具", "Tableware, kitchenware, other household articles of plastics", "千克", 0, 13, 13, "A", "塑料餐具,塑料杯,塑料碗,plastic tableware"),
    ("3926", 4, "其他塑料制品", "Other articles of plastics", "千克", 0, 13, 13, "A", "塑料制品,塑料零件,plastic products,plastic parts"),
    ("4011", 4, "新充气橡胶轮胎", "New pneumatic tyres, of rubber", "条", 0, 13, 13, "A", "轮胎,橡胶轮胎,tire,tyre"),
    ("4016", 4, "其他硫化橡胶制品", "Other vulcanised rubber articles", "千克", 0, 13, 13, "A", "橡胶制品,橡胶垫,橡胶管,rubber products"),

    # === 钢铁金属 ===
    ("7208", 4, "热轧卷材（钢板）", "Hot-rolled products of iron or non-alloy steel, in coils", "千克", 0, 13, 0, "A", "热轧钢板,热轧卷板,hot rolled steel"),
    ("7209", 4, "冷轧卷材（钢板）", "Cold-rolled products of iron or non-alloy steel, in coils", "千克", 0, 13, 0, "A", "冷轧钢板,冷轧卷板,cold rolled steel"),
    ("7210", 4, "镀层或涂层的钢板", "Flat-rolled products of iron or non-alloy steel, plated or coated", "千克", 0, 13, 0, "A", "镀锌板,镀锡板,涂层钢板,galvanized steel"),
    ("7214", 4, "热轧棒材", "Bars and rods, hot-rolled, of iron or non-alloy steel", "千克", 0, 13, 0, "A", "圆钢,螺纹钢,热轧棒材,steel bar,rebar"),
    ("7216", 4, "型材", "Angles, shapes and sections, of iron or non-alloy steel", "千克", 0, 13, 0, "A", "角钢,槽钢,H型钢,型钢,angle steel,channel steel"),
    ("7217", 4, "钢丝", "Wire of iron or non-alloy steel", "千克", 0, 13, 0, "A", "钢丝,铁丝,steel wire,iron wire"),
    ("7219", 4, "不锈钢板材", "Flat-rolled products of stainless steel", "千克", 0, 13, 0, "A", "不锈钢板,不锈钢卷板,stainless steel plate"),
    ("7304", 4, "钢铁管子", "Tubes, pipes and hollow profiles of iron or steel", "千克", 0, 13, 0, "A", "钢管,无缝钢管,焊接钢管,steel pipe,steel tube"),
    ("7307", 4, "钢铁管子附件", "Tube or pipe fittings of iron or steel", "千克", 0, 13, 0, "A", "管件,弯头,法兰,三通,pipe fitting,flange,elbow"),
    ("7308", 4, "钢铁结构体及部件", "Structures and parts of structures, of iron or steel", "千克", 0, 13, 0, "A", "钢结构,钢梁,钢柱,steel structure"),
    ("7310", 4, "钢铁容器", "Tanks, casks, drums, cans of iron or steel", "个", 0, 13, 0, "A", "铁桶,钢罐,铁罐,steel drum,steel tank"),
    ("7318", 4, "螺丝、螺栓、螺母", "Screws, bolts, nuts, rivets", "千克", 0, 13, 0, "A", "螺丝,螺栓,螺母,铆钉,screw,bolt,nut,rivet"),
    ("7326", 4, "其他钢铁制品", "Other articles of iron or steel", "千克", 0, 13, 0, "A", "钢铁制品,铁制品,钢制品,iron products,steel products"),
    ("7606", 4, "铝板、铝片", "Aluminium plates, sheets and strip", "千克", 0, 13, 0, "A", "铝板,铝片,铝合金板,aluminium sheet,aluminum plate"),
    ("7607", 4, "铝箔", "Aluminium foil", "千克", 0, 13, 0, "A", "铝箔,锡纸,aluminium foil"),
    ("7610", 4, "铝结构体", "Aluminium structures and parts", "千克", 0, 13, 0, "A", "铝合金门窗,铝型材,aluminium profile"),
    ("7616", 4, "其他铝制品", "Other articles of aluminium", "千克", 0, 13, 0, "A", "铝制品,铝合金制品,aluminium products"),

    # === 化工类（部分高频） ===
    ("2804", 4, "碳;氢", "Carbon, hydrogen", "千克", 0, 13, 0, "A", "碳,石墨,氢气,carbon,graphite,hydrogen"),
    ("2805", 4, "碱金属;碱土金属", "Alkali or alkaline-earth metals", "千克", 0, 13, 0, "A", "钠,钾,钙,镁,sodium,potassium,calcium,magnesium"),
    ("2806", 4, "氯化氢", "Hydrogen chloride", "千克", 0, 13, 0, "A", "盐酸,氯化氢,hydrochloric acid"),
    ("2807", 4, "硫酸;发烟硫酸", "Sulphuric acid; oleum", "千克", 0, 13, 0, "A", "硫酸,sulfuric acid"),
    ("2808", 4, "硝酸", "Nitric acid; sulphonitric acids", "千克", 0, 13, 0, "A", "硝酸,nitric acid"),
    ("2814", 4, "氨;氨水", "Ammonia; ammonia in aqueous solution", "千克", 0, 13, 0, "A", "氨,氨水,液氨,ammonia"),
    ("2815", 4, "氢氧化钠;氢氧化钾", "Sodium hydroxide; potassium hydroxide", "千克", 0, 13, 0, "A", "烧碱,氢氧化钠,氢氧化钾,火碱,sodium hydroxide,caustic soda"),
    ("2818", 4, "人造刚玉;氧化铝", "Artificial corundum; aluminium oxide", "千克", 0, 13, 0, "A", "氧化铝,刚玉,铝矾土,aluminium oxide,alumina"),
    ("2827", 4, "氯化物;溴化物", "Chlorides, bromides and iodides", "千克", 0, 13, 0, "A", "氯化钠,氯化钾,氯化钙,氯化铵,sodium chloride"),
    ("2836", 4, "碳酸盐", "Carbonates; peroxocarbonates", "千克", 0, 13, 0, "A", "碳酸钠,碳酸钙,碳酸钾,纯碱,sodium carbonate"),
    ("2837", 4, "氰化物", "Cyanides, cyanide oxides and complex cyanides", "千克", 0, 13, 0, "A", "氰化钠,氰化钾,氰化物,cyanide"),
    ("2844", 4, "放射性化学元素", "Radioactive chemical elements and isotopes", "千克", 0, 13, 0, "A", "铀,钚,放射性元素,uranium,plutonium"),
    ("2845", 4, "稀土金属", "Isotopes not elsewhere specified or included", "千克", 0, 13, 0, "A", "稀土,稀土金属,rare earth"),
    ("2846", 4, "稀土化合物", "Compounds of rare-earth metals, of yttrium or of scandium", "千克", 0, 13, 0, "A", "稀土化合物,氧化稀土,rare earth compounds"),
    ("2847", 4, "过氧化氢", "Hydrogen peroxide", "千克", 0, 13, 0, "A", "双氧水,过氧化氢,hydrogen peroxide"),
    ("2902", 4, "环烃", "Cyclic hydrocarbons", "千克", 0, 13, 0, "A", "苯,甲苯,二甲苯,苯乙烯,benzene,toluene,xylene"),
    ("2903", 4, "卤化烃", "Halogenated derivatives of hydrocarbons", "千克", 0, 13, 0, "A", "氯乙烯,二氯甲烷,三氯乙烯,halogenated hydrocarbons"),
    ("2905", 4, "醇类", "Acyclic alcohols and their halogenated derivatives", "千克", 0, 13, 0, "A", "甲醇,乙醇,丙醇,丁醇,methanol,ethanol"),
    ("2907", 4, "酚类", "Phenols; phenol-alcohols", "千克", 0, 13, 0, "A", "苯酚,甲酚,间苯二酚,phenol,cresol"),
    ("2908", 4, "醛类", "Ethers; ether-alcohols; ether-phenols", "千克", 0, 13, 0, "A", "甲醛,乙醛,苯甲醛,formaldehyde,acetaldehyde"),
    ("2909", 4, "醚类", "Ether-alcohols; ether-phenols; ether-esters", "千克", 0, 13, 0, "A", "乙醚,环氧乙烷,环氧丙烷,ether,ethylene oxide"),
    ("2914", 4, "酮及醌", "Ketones and quinones", "千克", 0, 13, 0, "A", "丙酮,丁酮,环己酮,acetone,MEK"),
    ("2915", 4, "羧酸", "Saturated acyclic monocarboxylic acids", "千克", 0, 13, 0, "A", "甲酸,乙酸,丙酸,丁酸,formic acid,acetic acid"),
    ("2916", 4, "不饱和羧酸", "Unsaturated monocarboxylic acids", "千克", 0, 13, 0, "A", "丙烯酸,甲基丙烯酸,acrylic acid,methacrylic acid"),
    ("2917", 4, "多元羧酸", "Polycarboxylic acids", "千克", 0, 13, 0, "A", "草酸,己二酸,柠檬酸,oxalic acid,adipic acid,citric acid"),
    ("2921", 4, "胺类", "Amino-compounds", "千克", 0, 13, 0, "A", "乙胺,丙胺,丁胺,苯胺,amine,aniline"),
    ("2924", 4, "酰胺类", "Carboxylic acid amides", "千克", 0, 13, 0, "A", "尿素,乙酰胺,甲酰胺,urea,acetamide"),
    ("2926", 4, "腈类", "Nitrile-function compounds", "千克", 0, 13, 0, "A", "丙烯腈,乙腈,己二腈,acrylonitrile,acetonitrile"),
    ("2928", 4, "有机肼类", "Organo-inorganic compounds, hydrazines", "千克", 0, 13, 0, "A", "肼,联氨,水合肼,hydrazine"),
    ("2930", 4, "有机硫化合物", "Organo-sulphur compounds", "千克", 0, 13, 0, "A", "二硫化碳,硫脲,有机硫化合物"),
    ("2933", 4, "杂环化合物", "Heterocyclic compounds with nitrogen hetero-atom(s) only", "千克", 0, 13, 0, "A", "吡啶,嘧啶,吡咯,咪唑,三唑,heterocyclic compounds"),
    ("2937", 4, "激素", "Hormones, natural or reproduced by synthesis", "千克", 0, 13, 0, "A", "激素,胰岛素,荷尔蒙,hormone,insulin"),
    ("2939", 4, "生物碱", "Alkaloids, natural or reproduced by synthesis", "千克", 0, 13, 0, "A", "生物碱,吗啡,可卡因,咖啡因,alkaloid,morphine,caffeine"),
    ("2941", 4, "抗生素", "Antibiotics", "千克", 0, 13, 0, "A", "抗生素,青霉素,头孢,阿莫西林,antibiotic,penicillin"),

    # === 医药 ===
    ("3001", 4, "人血;疫苗;毒素", "Human blood; animal blood; vaccines, toxins", "千克", 0, 9, 13, "AQ", "疫苗,血清,毒素,vaccine,serum,toxin"),
    ("3002", 4, "人血或动物血制品", "Human or animal blood or blood products", "千克", 0, 9, 13, "AQ", "血液制品,血浆,白蛋白,blood products,plasma,albumin"),
    ("3003", 4, "混合药品", "Medicaments consisting of two or more constituents", "千克", 0, 9, 13, "Q", "混合药品,复方药,medicaments"),
    ("3004", 4, "混合药品（已配定剂量）", "Medicaments consisting of mixed or unmixed products, in dosage", "千克", 0, 9, 13, "Q", "药品,成药,药片,胶囊,medicine,tablet,capsule"),
    ("3005", 4, "药棉、纱布、绷带", "Wadding, gauze, bandages", "千克", 0, 13, 13, "A", "药棉,纱布,绷带,医用敷料,gauze,bandage"),

    # === 食品 ===
    ("0201", 4, "鲜、冷牛肉", "Meat of bovine animals, fresh or chilled", "千克", 0, 9, 9, "ABQ", "牛肉,鲜牛肉,冷牛肉,beef"),
    ("0203", 4, "鲜、冷猪肉", "Meat of swine, fresh or chilled", "千克", 0, 9, 9, "ABQ", "猪肉,鲜猪肉,pork"),
    ("0207", 4, "家禽肉", "Meat and edible offal of poultry", "千克", 0, 9, 9, "ABQ", "鸡肉,鸭肉,鹅肉,chicken,duck,poultry"),
    ("0302", 4, "鲜、冷鱼", "Fish, fresh or chilled", "千克", 0, 9, 9, "ABQ", "鲜鱼,冷鱼,fresh fish"),
    ("0401", 4, "未浓缩乳及奶油", "Milk and cream, not concentrated", "千克", 0, 9, 9, "AB", "牛奶,鲜牛奶,奶油,milk,cream"),
    ("0407", 4, "禽蛋", "Birds' eggs, in shell, fresh", "千克", 0, 9, 9, "AB", "鸡蛋,鸭蛋,eggs"),
    ("0803", 4, "香蕉", "Bananas, including plantains", "千克", 0, 9, 9, "A", "香蕉,banana"),
    ("0901", 4, "咖啡", "Coffee, whether or not roasted", "千克", 0, 13, 13, "AB", "咖啡,咖啡豆,coffee"),
    ("0902", 4, "茶", "Tea, whether or not flavoured", "千克", 0, 9, 13, "AB", "茶叶,绿茶,红茶,乌龙茶,tea,green tea,black tea"),
    ("1001", 4, "小麦", "Wheat and meslin", "千克", 0, 9, 9, "AB", "小麦,wheat"),
    ("1005", 4, "玉米", "Maize (corn)", "千克", 0, 9, 9, "AB", "玉米,玉米粒,corn,maize"),
    ("1006", 4, "大米", "Rice", "千克", 0, 9, 9, "AB", "大米,稻谷,rice"),
    ("1201", 4, "大豆", "Soya beans", "千克", 0, 9, 9, "AB", "大豆,黄豆,soybean,soya"),
    ("1207", 4, "其他含油子仁", "Other oil seeds and oleaginous fruits", "千克", 0, 9, 9, "A", "花生,芝麻,葵花籽,peanut,sunflower seed"),
    ("1511", 4, "棕榈油", "Palm oil and its fractions", "千克", 0, 9, 9, "AB", "棕榈油,palm oil"),
    ("1507", 4, "豆油", "Soya-bean oil and its fractions", "千克", 0, 9, 9, "AB", "大豆油,豆油,soybean oil"),

    # === 家具家居 ===
    ("9401", 4, "座椅", "Seats (other than those of heading 9402)", "个", 0, 13, 13, "A", "椅子,沙发,座椅,chair,sofa,seat"),
    ("9403", 4, "其他家具", "Other furniture and parts thereof", "个", 0, 13, 13, "A", "桌子,柜子,床,书架,家具,table,desk,cabinet,bed,furniture"),
    ("940330", 6, "木制办公家具", "Wooden furniture of a kind used in offices", "个", 0, 13, 13, "A", "办公桌,办公家具,木制家具,office desk,office furniture"),
    ("940350", 6, "木制卧室家具", "Wooden furniture of a kind used in the bedroom", "个", 0, 13, 13, "A", "木床,衣柜,床头柜,bedroom furniture"),
    ("9405", 4, "灯具及照明装置", "Lamps and lighting fittings", "个", 0, 13, 13, "A", "吊灯,台灯,壁灯,灯泡,LED灯,lamp,lighting,ceiling light"),

    # === 玩具 ===
    ("9503", 4, "玩具、模型", "Toys, games and sports requisites", "千克", 0, 13, 13, "A", "玩具,毛绒玩具,积木,模型,toy,plush toy,building blocks"),
    ("9506", 4, "运动用品", "Sports equipment", "千克", 0, 13, 13, "A", "高尔夫球杆,运动器材,golf club,sports equipment"),
    ("9507", 4, "钓鱼竿", "Fishing rods, fish-hooks and other fishing tackle", "千克", 0, 13, 13, "A", "钓鱼竿,渔具,fishing rod,fishing tackle"),

    # === 陶瓷玻璃 ===
    ("6907", 4, "瓷砖", "Ceramic flags and paving, hearth or wall tiles", "平方米", 0, 13, 13, "A", "瓷砖,地砖,墙砖,ceramic tile"),
    ("6911", 4, "陶瓷餐具", "Tableware, kitchenware of porcelain or china", "千克", 0, 13, 13, "A", "瓷碗,瓷盘,瓷杯,陶瓷餐具,ceramic tableware"),
    ("7003", 4, "铸制或轧制玻璃板", "Glass in sheets, cast or rolled", "平方米", 0, 13, 13, "A", "玻璃板,钢化玻璃,玻璃,glass sheet,tempered glass"),
    ("7005", 4, "浮法玻璃", "Float glass and surface ground glass", "平方米", 0, 13, 13, "A", "浮法玻璃,建筑玻璃,float glass"),
    ("7007", 4, "安全玻璃", "Safety glass", "平方米", 0, 13, 13, "A", "钢化玻璃,夹层玻璃,安全玻璃,safety glass,laminated glass"),
    ("7013", 4, "玻璃器皿", "Glassware of a kind used for table or kitchen", "千克", 0, 13, 13, "A", "玻璃杯,玻璃碗,玻璃器皿,glass cup,glassware"),

    # === 纸制品 ===
    ("4802", 4, "书写印刷纸", "Uncoated paper and paperboard, of a kind used for writing", "千克", 0, 9, 13, "A", "打印纸,复印纸,书写纸,printing paper,A4 paper"),
    ("4803", 4, "卫生纸", "Toilet paper", "千克", 0, 9, 13, "A", "卫生纸,卷纸,toilet paper"),
    ("4804", 4, "牛皮纸", "Kraft paper and paperboard", "千克", 0, 9, 13, "A", "牛皮纸,kraft paper"),
    ("4805", 4, "瓦楞纸", "Corrugated paper and paperboard", "千克", 0, 9, 13, "A", "瓦楞纸,瓦楞纸板,corrugated paper"),
    ("4810", 4, "涂布纸", "Paper and paperboard, coated", "千克", 0, 9, 13, "A", "铜版纸,涂布纸,coated paper"),
    ("4819", 4, "纸箱、纸盒", "Cartons, boxes, cases, bags of paper", "千克", 0, 9, 13, "A", "纸箱,纸盒,纸袋,纸包装,cardboard box,paper bag"),
    ("4820", 4, "纸制文具", "Registers, account books, notebooks, order books", "千克", 0, 9, 13, "A", "笔记本,练习本,日记本,notebook,exercise book"),

    # === 石材建材 ===
    ("2516", 4, "花岗岩", "Granite, porphyry, basalt, sandstone", "千克", 0, 13, 0, "A", "花岗岩,大理石,石材,granite,marble,stone"),
    ("2523", 4, "水泥", "Portland cement, aluminous cement", "千克", 0, 13, 0, "A", "水泥,硅酸盐水泥,cement"),

    # === 光学仪器 ===
    ("9001", 4, "光纤、光缆", "Optical fibres, optical fibre bundles", "千克", 0, 13, 13, "A", "光纤,光缆,optical fiber,optical cable"),
    ("9003", 4, "眼镜架及眼镜片", "Frames and mountings for spectacles", "个", 0, 13, 13, "A", "眼镜,镜架,镜片,glasses,spectacles,eyewear"),
    ("9004", 4, "矫正视力用眼镜", "Spectacles, goggles and the like, corrective", "副", 0, 13, 13, "A", "近视眼镜,老花镜,prescription glasses"),
    ("9005", 4, "双筒望远镜", "Binoculars, monoculars, other optical telescopes", "个", 0, 13, 13, "A", "望远镜,双筒望远镜,binoculars,telescope"),
    ("9006", 4, "照相机", "Photographic cameras", "台", 0, 13, 13, "A", "照相机,数码相机,camera,digital camera"),
    ("9008", 4, "投影仪", "Image projectors", "台", 0, 13, 13, "A", "投影仪,幻灯机,projector"),
    ("9009", 4, "复印机", "Photocopying apparatus", "台", 0, 13, 13, "A", "复印机,photocopier"),
    ("9011", 4, "显微镜", "Compound optical microscopes", "台", 0, 13, 13, "A", "显微镜,microscope"),
    ("9013", 4, "激光器", "Liquid crystal devices; lasers", "台", 0, 13, 13, "A", "激光器,laser"),
    ("9014", 4, "导航仪器", "Direction finding compasses; navigational instruments", "台", 0, 13, 13, "A", "导航仪,指南针,罗盘,compass,navigation instrument"),
    ("9015", 4, "测量仪器", "Surveying, hydrographic, oceanographic, hydrological instruments", "台", 0, 13, 13, "A", "测量仪器,经纬仪,水平仪,surveying instrument"),
    ("9016", 4, "天平", "Balances of a sensitivity of 0.1mg or better", "台", 0, 13, 13, "A", "天平,分析天平,精密天平,balance,analytical balance"),
    ("9018", 4, "医疗、外科、牙科仪器", "Instruments and appliances used in medical, surgical, dental", "台", 0, 13, 13, "A", "医疗仪器,手术器械,牙科器械,medical instrument,surgical instrument"),
    ("9020", 4, "其他呼吸器具", "Other breathing appliances and gas masks", "个", 0, 13, 13, "A", "呼吸器,防毒面具,gas mask,respirator"),
    ("9022", 4, "X射线设备", "Apparatus based on X-rays", "台", 0, 13, 13, "A", "X光机,X射线设备,X-ray equipment"),
    ("9025", 4, "温度计", "Thermometers and pyrometers", "个", 0, 13, 13, "A", "温度计,测温仪,thermometer"),
    ("9026", 4, "液体流量计", "Instruments for measuring or checking the flow of liquids", "个", 0, 13, 13, "A", "流量计,液位计,flow meter"),
    ("9027", 4, "理化分析仪器", "Instruments and apparatus for physical or chemical analysis", "台", 0, 13, 13, "A", "分析仪器,色谱仪,光谱仪,analyzer,spectrometer"),
    ("9028", 4, "电量测量仪器", "Gas, liquid or electricity supply or production meters", "个", 0, 13, 13, "A", "电表,水表,气表,gas meter,water meter"),
    ("9030", 4, "示波器", "Oscilloscopes, spectrum analysers", "台", 0, 13, 13, "A", "示波器,频谱分析仪,oscilloscope"),
    ("9031", 4, "测量或检验仪器", "Measuring or checking instruments", "台", 0, 13, 13, "A", "测量仪器,检测设备,measuring instrument"),

    # === 钟表 ===
    ("9102", 4, "手表", "Wrist watches, pocket watches", "个", 0, 13, 13, "A", "手表,腕表,石英表,机械表,watch,wristwatch"),
    ("9105", 4, "闹钟", "Other clocks, wall clocks, etc.", "个", 0, 13, 13, "A", "闹钟,挂钟,钟,clock,alarm clock"),

    # === 乐器 ===
    ("9201", 4, "钢琴", "Pianos, including automatic pianos", "台", 0, 13, 13, "A", "钢琴,piano"),
    ("9205", 4, "管乐器", "Wind instruments", "个", 0, 13, 13, "A", "萨克斯,长笛,小号,wind instrument,saxophone,flute"),
    ("9207", 4, "电子乐器", "Electronic musical instruments", "台", 0, 13, 13, "A", "电子琴,电子鼓,电子乐器,electronic musical instrument"),

    # === 武器 ===
    ("9301", 4, "军用武器", "Military weapons", "件", 0, 13, 13, "A", "枪支,武器,步枪,手枪,firearm,rifle,pistol"),
    ("9302", 4, "弹药", "Ammunition and projectiles", "千克", 0, 13, 13, "A", "弹药,子弹,炮弹,ammunition,bullet"),

    # === 矿产 ===
    ("2601", 4, "铁矿砂", "Iron ores and concentrates", "千克", 0, 13, 0, "A", "铁矿石,铁矿砂,iron ore"),
    ("2603", 4, "铜矿砂", "Copper ores and concentrates", "千克", 0, 13, 0, "A", "铜矿石,铜矿砂,copper ore"),
    ("2606", 4, "铝矿砂", "Aluminium ores and concentrates", "千克", 0, 13, 0, "A", "铝土矿,铝矿石,bauxite,aluminium ore"),
    ("2612", 4, "铀矿砂", "Uranium or thorium ores and concentrates", "千克", 0, 13, 0, "A", "铀矿石,钍矿石,uranium ore,thorium ore"),
    ("2616", 4, "贵金属矿砂", "Precious metal ores and concentrates", "千克", 0, 13, 0, "A", "金矿石,银矿石,铂矿石,gold ore,silver ore"),
    ("2701", 4, "煤炭", "Coal; briquettes, ovoids and similar solid fuels", "千克", 0, 13, 0, "A", "煤,煤炭,无烟煤,烟煤,coal"),
    ("2709", 4, "原油", "Petroleum oils and oils obtained from bituminous minerals, crude", "千克", 0, 13, 0, "A", "原油,石油,crude oil,petroleum"),
    ("2710", 4, "成品油", "Petroleum oils and oils from bituminous minerals", "千克", 0, 13, 0, "A", "汽油,柴油,煤油,燃料油,gasoline,diesel,kerosene"),
    ("2711", 4, "天然气", "Petroleum gases and other gaseous hydrocarbons", "千克", 0, 9, 0, "A", "天然气,液化石油气,液化天然气,natural gas,LNG,LPG"),

    # === 木制品 ===
    ("4403", 4, "原木", "Wood in the rough, whether or not stripped of bark", "立方米", 0, 9, 0, "AB", "原木,木材,logs,timber"),
    ("4407", 4, "锯材", "Wood sawn or chipped lengthwise", "立方米", 0, 9, 0, "AB", "木板,木方,锯材,lumber,sawn wood"),
    ("4411", 4, "纤维板", "Fibreboard of wood", "立方米", 0, 13, 13, "A", "密度板,纤维板,MDF,fibreboard"),
    ("4412", 4, "胶合板", "Plywood, veneered panels", "立方米", 0, 13, 13, "A", "胶合板,多层板,plywood"),
    ("4413", 4, "木制碎料板", "Densified wood, particle board", "立方米", 0, 13, 13, "A", "刨花板,颗粒板,particle board"),
    ("4418", 4, "建筑用木制品", "Builder's joinery and carpentry of wood", "千克", 0, 13, 13, "A", "木门,木窗,木地板,wooden door,wooden floor"),

    # === 珠宝 ===
    ("7102", 4, "钻石", "Diamonds", "克拉", 0, 13, 0, "A", "钻石,diamond"),
    ("7103", 4, "宝石（不含钻石）", "Precious stones (other than diamonds)", "克拉", 0, 13, 0, "A", "红宝石,蓝宝石,祖母绿,ruby,sapphire,emerald"),
    ("7104", 4, "半宝石", "Synthetic or reconstructed precious or semi-precious stones", "克拉", 0, 13, 0, "A", "水晶,玛瑙,翡翠,jade,crystal,agate"),
    ("7108", 4, "黄金", "Gold (including gold plated with platinum)", "克", 0, 13, 0, "A", "黄金,金条,金币,gold,gold bar"),
    ("7106", 4, "白银", "Silver (including silver plated with gold)", "克", 0, 13, 0, "A", "白银,银条,silver,silver bar"),
    ("7110", 4, "铂金", "Platinum", "克", 0, 13, 0, "A", "铂金,白金,platinum"),
    ("7113", 4, "珠宝首饰", "Articles of jewellery and parts thereof", "千克", 0, 13, 13, "A", "珠宝,首饰,项链,戒指,jewelry,necklace,ring"),

    # === 其他 ===
    ("3303", 4, "香水", "Perfumes and toilet waters", "千克", 0, 13, 13, "A", "香水,古龙水,perfume,cologne"),
    ("3304", 4, "化妆品", "Beauty or make-up preparations", "千克", 0, 13, 13, "A", "化妆品,口红,粉底,睫毛膏,cosmetics,lipstick,foundation"),
    ("3305", 4, "护发品", "Preparations for the hair", "千克", 0, 13, 13, "A", "洗发水,护发素,发胶,shampoo,hair conditioner"),
    ("3401", 4, "肥皂", "Soap; organic surface-active products", "千克", 0, 13, 13, "A", "肥皂,香皂,洗手液,soap,hand sanitizer"),
    ("3402", 4, "洗涤剂", "Surface-active preparations", "千克", 0, 13, 13, "A", "洗衣液,洗洁精,洗涤剂,detergent,laundry detergent"),
    ("3601", 4, "火药", "Gunpowder", "千克", 0, 13, 13, "A", "火药,黑火药,gunpowder"),
    ("3602", 4, "炸药", "Prepared explosives", "千克", 0, 13, 13, "A", "炸药,TNT,dynamite,explosives"),
    ("3604", 4, "烟花", "Fireworks, signalling flares", "千克", 0, 13, 13, "A", "烟花,爆竹,鞭炮,fireworks,firecrackers"),
    ("5603", 4, "无纺织物", "Nonwovens, whether or not impregnated", "千克", 0, 13, 13, "A", "无纺布,不织布,nonwoven fabric"),
    ("5001", 4, "生丝", "Silk, not thrown", "千克", 0, 13, 13, "A", "生丝,蚕丝,raw silk"),
    ("5101", 4, "羊毛", "Wool, not carded or combed", "千克", 0, 13, 13, "A", "羊毛,原毛,wool"),
    ("5201", 4, "原棉", "Cotton, not carded or combed", "千克", 0, 13, 13, "A", "棉花,原棉,raw cotton"),
    ("5205", 4, "棉纱线", "Yarn of cotton", "千克", 0, 13, 13, "A", "棉纱,棉线,cotton yarn"),
    ("5208", 4, "棉织物", "Woven fabrics of cotton", "米", 0, 13, 13, "A", "棉布,棉织物,cotton fabric"),
    ("6601", 4, "雨伞", "Umbrellas, sun umbrellas", "把", 0, 13, 13, "A", "雨伞,太阳伞,umbrella"),
    ("6704", 4, "假发", "Wigs, false beards, eyebrows and eyelashes", "千克", 0, 13, 13, "A", "假发,假睫毛,wig,false eyelashes"),
]

# ============================================================
# 8位本国子目编码（由6位编码扩展）
# 格式: (编码, 层级, 中文描述, 英文描述, 单位, 关税, 增值税, 退税率, 监管条件, 搜索关键词)
# ============================================================
CN_8DIGIT_CODES = [
    # === 电子电气类 8位 ===
    ("84713000", 8, "便携式自动数据处理设备，重量≤10kg", "Portable digital ADP machines, weight ≤10kg", "台", 0, 13, 13, "A", "笔记本电脑,便携电脑,laptop,notebook"),
    ("84714100", 8, "其他自动数据处理设备", "Other ADP machines", "台", 0, 13, 13, "A", "台式电脑,一体机,desktop"),
    ("84714900", 8, "其他自动数据处理系统", "Other ADP systems", "台", 0, 13, 13, "A", "工作站,服务器,workstation"),
    ("84715000", 8, "自动数据处理设备的部件", "ADP units", "台", 0, 13, 13, "A", "电脑配件,硬盘,光驱"),
    ("84717000", 8, "存储部件", "Storage units", "台", 0, 13, 13, "A", "硬盘,固态硬盘,U盘,SSD"),
    ("85044000", 8, "静止式变流器", "Static converters", "个", 0, 13, 13, "A", "电源适配器,充电器,变压器"),
    ("85076000", 8, "锂离子蓄电池", "Lithium-ion batteries", "个", 0, 13, 13, "A", "锂电池,锂离子电池,battery"),
    ("85171200", 8, "其他电话机", "Other telephone sets", "台", 0, 13, 13, "A", "电话机,座机,telephone"),
    ("85171300", 8, "智能手机", "Smartphones", "台", 0, 13, 13, "A", "智能手机,手机,smartphone"),
    ("85176200", 8, "接收、转换和发送设备", "Reception/conversion/transmission equipment", "台", 0, 13, 13, "A", "路由器,交换机,网络设备"),
    ("85177000", 8, "电话机及其他设备的零件", "Parts of telephone sets", "千克", 0, 13, 13, "A", "手机零件,电话零件"),
    ("85182100", 8, "单喇叭音箱", "Single loudspeaker", "个", 0, 13, 13, "A", "音箱,喇叭,speaker"),
    ("85182900", 8, "多喇叭音箱", "Multiple loudspeakers", "个", 0, 13, 13, "A", "音箱,音响,speaker"),
    ("85183000", 8, "耳机", "Headphones", "个", 0, 13, 13, "A", "耳机,耳麦,headphone,earphone"),
    ("85235100", 8, "固态非易失性存储器件", "Solid-state non-volatile storage devices", "个", 0, 13, 13, "A", "闪存卡,SD卡,U盘,flash"),
    ("85251000", 8, "无线电话发送设备", "Radio telephonic transmission equipment", "台", 0, 13, 13, "A", "对讲机,无线发射器"),
    ("85258100", 8, "雷达设备", "Radar apparatus", "台", 0, 13, 13, "A", "雷达,radar"),
    ("85258900", 8, "其他激光器", "Other lasers", "台", 0, 13, 13, "A", "激光器,laser"),
    ("85286200", 8, "其他监视器", "Other monitors", "台", 0, 13, 13, "A", "显示器,监视器,monitor"),
    ("85287200", 8, "彩色电视接收装置", "Color television receivers", "台", 0, 13, 13, "A", "彩色电视,电视机,TV"),
    ("85340000", 8, "印刷电路板", "Printed circuits", "千克", 0, 13, 13, "A", "PCB,电路板,印刷电路板"),
    ("85411000", 8, "发光二极管(LED)", "Light-emitting diodes (LED)", "个", 0, 13, 13, "A", "LED,发光二极管"),
    ("85412100", 8, "耗散功率小于1W的晶体管", "Transistors, dissipation <1W", "个", 0, 13, 13, "A", "晶体管,三极管,transistor"),
    ("85414000", 8, "太阳能电池", "Solar cells", "个", 0, 13, 13, "A", "太阳能电池,光伏板,solar cell"),
    ("85423100", 8, "处理器及控制器", "Processors and controllers", "个", 0, 13, 13, "A", "CPU,处理器,芯片"),
    ("85423200", 8, "存储器", "Memories", "个", 0, 13, 13, "A", "内存,存储器,RAM,memory"),
    ("85423300", 8, "放大器", "Amplifiers", "个", 0, 13, 13, "A", "放大器,amplifier"),
    ("85423900", 8, "其他集成电路", "Other integrated circuits", "个", 0, 13, 13, "A", "集成电路,IC,芯片,integrated circuit"),
    # === 汽车类 8位 ===
    ("87032300", 8, "汽油型小轿车，排量1000ml-1500ml", "Petrol cars 1000-1500cc", "辆", 15, 13, 13, "4AB", "小轿车,轿车,car"),
    ("87032400", 8, "汽油型小轿车，排量1500ml-3000ml", "Petrol cars 1500-3000cc", "辆", 15, 13, 13, "4AB", "小轿车,轿车,car"),
    ("87089900", 8, "其他汽车零件及附件", "Other motor vehicle parts", "千克", 6, 13, 13, "", "汽车配件,汽车零件"),
    # === 纺织服装类 8位 ===
    ("42022100", 8, "皮革制手提包", "Handbags of leather", "个", 0, 13, 13, "A", "皮包,手提包,handbag"),
    ("42022200", 8, "塑料制手提包", "Handbags of plastics", "个", 0, 13, 13, "A", "塑料包,手提包"),
    ("42022900", 8, "纺织材料制手提包", "Handbags of textile materials", "个", 0, 13, 13, "A", "布包,手提包"),
    ("42023100", 8, "纺织材料制背包", "Backpacks of textile materials", "个", 0, 13, 13, "A", "背包,双肩包,backpack"),
    ("42023200", 8, "塑料制背包", "Backpacks of plastics", "个", 0, 13, 13, "A", "背包,双肩包"),
    ("42029100", 8, "皮革制背包", "Backpacks of leather", "个", 0, 13, 13, "A", "皮背包,背包"),
    ("42029200", 8, "塑料制箱包", "Plastic suitcase", "个", 0, 13, 13, "A", "塑料箱,行李箱"),
    ("42031000", 8, "皮革制衣箱", "Suitcases of leather", "个", 0, 13, 13, "A", "皮箱,行李箱,suitcase"),
    ("52081100", 8, "棉织物，未漂白", "Cotton fabrics, unbleached", "米", 0, 13, 13, "A", "棉布,棉织物"),
    ("52081200", 8, "棉织物，漂白", "Cotton fabrics, bleached", "米", 0, 13, 13, "A", "棉布,漂白棉"),
    ("52081300", 8, "棉织物，染色", "Cotton fabrics, dyed", "米", 0, 13, 13, "A", "棉布,染色棉"),
    ("52081900", 8, "其他棉织物", "Other cotton fabrics", "米", 0, 13, 13, "A", "棉布,棉织物"),
    ("52082100", 8, "棉织物，未漂白，每平米重≤200g", "Cotton fabrics, unbleached ≤200g/m²", "米", 0, 13, 13, "A", "棉布,薄棉布"),
    ("52082200", 8, "棉织物，漂白，每平米重≤200g", "Cotton fabrics, bleached ≤200g/m²", "米", 0, 13, 13, "A", "棉布,漂白棉布"),
    ("52082900", 8, "其他棉织物，每平米重≤200g", "Other cotton fabrics ≤200g/m²", "米", 0, 13, 13, "A", "棉布,薄棉布"),
    ("52083100", 8, "棉织物，未漂白，每平米重200-400g", "Cotton fabrics, unbleached 200-400g/m²", "米", 0, 13, 13, "A", "棉布,中厚棉布"),
    ("52083200", 8, "棉织物，漂白，每平米重200-400g", "Cotton fabrics, bleached 200-400g/m²", "米", 0, 13, 13, "A", "棉布,漂白棉布"),
    ("52083900", 8, "其他棉织物，每平米重200-400g", "Other cotton fabrics 200-400g/m²", "米", 0, 13, 13, "A", "棉布,中厚棉布"),
    ("52084100", 8, "棉织物，未漂白，每平米重>400g", "Cotton fabrics, unbleached >400g/m²", "米", 0, 13, 13, "A", "棉布,厚棉布"),
    ("52084200", 8, "棉织物，漂白，每平米重>400g", "Cotton fabrics, bleached >400g/m²", "米", 0, 13, 13, "A", "棉布,厚棉布"),
    ("52084900", 8, "其他棉织物，每平米重>400g", "Other cotton fabrics >400g/m²", "米", 0, 13, 13, "A", "棉布,厚棉布"),
    ("66011000", 8, "花园用伞", "Garden umbrellas", "把", 0, 13, 13, "A", "花园伞,遮阳伞"),
    ("66019100", 8, "折叠伞", "Folding umbrellas", "把", 0, 13, 13, "A", "折叠伞,雨伞"),
    ("66019900", 8, "其他雨伞", "Other umbrellas", "把", 0, 13, 13, "A", "雨伞,太阳伞"),
    ("67041100", 8, "合成纤维制假发", "Synthetic hair wigs", "千克", 0, 13, 13, "A", "假发,合成假发"),
    ("67041900", 8, "其他材料制假发", "Other wigs", "千克", 0, 13, 13, "A", "假发,人发假发"),
    ("67042000", 8, "假发零件", "Parts of wigs", "千克", 0, 13, 13, "A", "假发配件"),
    ("94031000", 8, "木制办公家具", "Wooden office furniture", "件", 0, 13, 13, "A", "办公桌,办公家具,书桌"),
    ("94033000", 8, "木制卧室家具", "Wooden bedroom furniture", "件", 0, 13, 13, "A", "床,衣柜,卧室家具"),
    ("94035000", 8, "木制厨房家具", "Wooden kitchen furniture", "件", 0, 13, 13, "A", "橱柜,厨房家具"),
    ("94036000", 8, "其他木制家具", "Other wooden furniture", "件", 0, 13, 13, "A", "木家具,实木家具"),
]

# ============================================================
# 10位完整海关编码（由8位编码进一步细分）
# 格式: (编码, 层级, 中文描述, 英文描述, 单位, 关税, 增值税, 退税率, 监管条件, 搜索关键词)
# ============================================================
CN_10DIGIT_CODES = [
    # === 电子电气类 10位 ===
    ("8471300000", 10, "便携式自动数据处理设备，重量≤10kg", "Portable digital ADP machines, ≤10kg", "台", 0, 13, 13, "A", "笔记本电脑,便携电脑,laptop"),
    ("8471300001", 10, "便携式自动数据处理设备-品牌机", "Portable ADP machines - branded", "台", 0, 13, 13, "A", "品牌笔记本,苹果,联想"),
    ("8471300090", 10, "便携式自动数据处理设备-其他", "Portable ADP machines - other", "台", 0, 13, 13, "A", "笔记本,便携电脑"),
    ("8471410000", 10, "其他自动数据处理设备", "Other ADP machines", "台", 0, 13, 13, "A", "台式电脑,一体机"),
    ("8471410001", 10, "其他自动数据处理设备-品牌机", "Other ADP machines - branded", "台", 0, 13, 13, "A", "品牌台式机"),
    ("8471410090", 10, "其他自动数据处理设备-其他", "Other ADP machines - other", "台", 0, 13, 13, "A", "台式电脑"),
    ("8471490000", 10, "其他自动数据处理系统", "Other ADP systems", "台", 0, 13, 13, "A", "工作站,服务器"),
    ("8471500000", 10, "自动数据处理设备的部件", "ADP units", "台", 0, 13, 13, "A", "电脑配件"),
    ("8471700000", 10, "存储部件", "Storage units", "台", 0, 13, 13, "A", "硬盘,SSD"),
    ("8507600000", 10, "锂离子蓄电池", "Lithium-ion batteries", "个", 0, 13, 13, "A", "锂电池"),
    ("8507600001", 10, "锂离子蓄电池-动力型", "Lithium-ion batteries - power type", "个", 0, 13, 13, "A", "动力电池,电动车电池"),
    ("8507600090", 10, "锂离子蓄电池-其他", "Lithium-ion batteries - other", "个", 0, 13, 13, "A", "锂电池,充电宝"),
    ("8517130000", 10, "智能手机", "Smartphones", "台", 0, 13, 13, "A", "智能手机,手机"),
    ("8517130001", 10, "智能手机-品牌机", "Smartphones - branded", "台", 0, 13, 13, "A", "苹果手机,三星手机"),
    ("8517130090", 10, "智能手机-其他", "Smartphones - other", "台", 0, 13, 13, "A", "智能手机"),
    ("8517700000", 10, "电话机及其他设备的零件", "Parts of telephone sets", "千克", 0, 13, 13, "A", "手机零件"),
    ("8518300000", 10, "耳机", "Headphones", "个", 0, 13, 13, "A", "耳机,蓝牙耳机"),
    ("8523510000", 10, "固态非易失性存储器件", "Solid-state storage devices", "个", 0, 13, 13, "A", "闪存卡,SD卡"),
    ("8528720000", 10, "彩色电视接收装置", "Color TV receivers", "台", 0, 13, 13, "A", "电视机,TV"),
    ("8534000000", 10, "印刷电路板", "Printed circuits", "千克", 0, 13, 13, "A", "PCB,电路板"),
    ("8541100000", 10, "发光二极管(LED)", "Light-emitting diodes", "个", 0, 13, 13, "A", "LED"),
    ("8542310000", 10, "处理器及控制器", "Processors and controllers", "个", 0, 13, 13, "A", "CPU,处理器"),
    ("8542310001", 10, "处理器及控制器-高端", "Processors - high-end", "个", 0, 13, 13, "A", "高端CPU,服务器CPU"),
    ("8542310090", 10, "处理器及控制器-其他", "Processors - other", "个", 0, 13, 13, "A", "CPU,处理器"),
    ("8542320000", 10, "存储器", "Memories", "个", 0, 13, 13, "A", "内存,存储器"),
    ("8542330000", 10, "放大器", "Amplifiers", "个", 0, 13, 13, "A", "放大器"),
    ("8542390000", 10, "其他集成电路", "Other integrated circuits", "个", 0, 13, 13, "A", "集成电路,芯片"),
    # === 汽车类 10位 ===
    ("8703230001", 10, "汽油型小轿车1000-1500ml-品牌", "Petrol cars 1000-1500cc branded", "辆", 15, 13, 13, "4AB", "品牌轿车"),
    ("8703230090", 10, "汽油型小轿车1000-1500ml-其他", "Petrol cars 1000-1500cc other", "辆", 15, 13, 13, "4AB", "小轿车"),
    ("8703240001", 10, "汽油型小轿车1500-3000ml-品牌", "Petrol cars 1500-3000cc branded", "辆", 15, 13, 13, "4AB", "品牌轿车"),
    ("8703240090", 10, "汽油型小轿车1500-3000ml-其他", "Petrol cars 1500-3000cc other", "辆", 15, 13, 13, "4AB", "小轿车"),
    # === 纺织服装类 10位 ===
    ("4202210000", 10, "皮革制手提包", "Leather handbags", "个", 0, 13, 13, "A", "皮包,手提包"),
    ("4202220000", 10, "塑料制手提包", "Plastic handbags", "个", 0, 13, 13, "A", "塑料包"),
    ("4202290000", 10, "纺织材料制手提包", "Textile handbags", "个", 0, 13, 13, "A", "布包"),
    ("4202310000", 10, "纺织材料制背包", "Textile backpacks", "个", 0, 13, 13, "A", "背包"),
    ("6601910000", 10, "折叠伞", "Folding umbrellas", "把", 0, 13, 13, "A", "折叠伞"),
    ("6704110000", 10, "合成纤维制假发", "Synthetic wigs", "千克", 0, 13, 13, "A", "假发"),
    ("9403100000", 10, "木制办公家具", "Wooden office furniture", "件", 0, 13, 13, "A", "办公桌,办公家具"),
    ("9403300000", 10, "木制卧室家具", "Wooden bedroom furniture", "件", 0, 13, 13, "A", "床,卧室家具"),
    ("9403500000", 10, "木制厨房家具", "Wooden kitchen furniture", "件", 0, 13, 13, "A", "橱柜"),
]


# ============================================================
# 中国两用物项清单数据（2024年版）
# 数据来源：商务部 工业和信息化部 海关总署 国家密码局
# 公告2024年第51号
# ============================================================

DUAL_USE_ITEMS = [
    # (类别, 子类别, 编号, 描述, 相关HS编码, 管控级别, 需要许可证, 备注)
    ("专用材料和相关设备", "化学制品", "1C001", "可用于化学武器生产的化学品（附表1）", "2804,2805,2806,2807,2808,2809,2810,2811,2812,2813,2814,2815,2816,2818,2825,2827,2833,2836,2837,2838,2839,2840,2841,2842,2843,2844,2845,2846,2847,2849,2850,2851,2852,2902,2903,2904,2905,2906,2907,2908,2909,2910,2911,2912,2914,2915,2916,2917,2918,2920,2921,2922,2923,2924,2925,2926,2927,2928,2929,2930,2931,2933,2934,2935,2937,2938,2939,2940,2941,2942", "严格管控", 1, "包括化学品武器前体"),
    ("专用材料和相关设备", "化学制品", "1C002", "可用于化学武器生产的化学品（附表2）", "2811,2812,2813,2814,2815,2816,2818,2825,2827,2833,2836,2837,2838,2839,2840,2841,2842,2843,2844,2845,2846,2847,2849,2850,2851,2852,2902,2903,2904,2905,2906,2907,2908,2909,2910,2911,2912,2914,2915,2916,2917,2918,2920,2921,2922,2923,2924,2925,2926,2927,2928,2929,2930,2931,2933,2934,2935,2937,2938,2939,2940,2941,2942", "严格管控", 1, "包括化学品武器前体"),
    ("专用材料和相关设备", "化学制品", "1C003", "可用于化学武器生产的化学品（附表3）", "2811,2812,2813,2814,2815,2816,2818,2825,2827,2833,2836,2837,2838,2839,2840,2841,2842,2843,2844,2845,2846,2847,2849,2850,2851,2852,2902,2903,2904,2905,2906,2907,2908,2909,2910,2911,2912,2914,2915,2916,2917,2918,2920,2921,2922,2923,2924,2925,2926,2927,2928,2929,2930,2931,2933,2934,2935,2937,2938,2939,2940,2941,2942", "严格管控", 1, "包括化学品武器前体"),
    ("专用材料和相关设备", "微生物及毒素", "1C350", "人、动物、植物病原体及其遗传物质", "3001,3002", "严格管控", 1, "包括生物武器制剂"),
    ("专用材料和相关设备", "微生物及毒素", "1C351", "毒素及亚单位", "3001", "严格管控", 1, "包括生物毒素"),
    ("材料加工", "特殊材料", "1C101", "碳纤维及相关材料", "6815,3926", "严格管控", 1, "用于航空航天和导弹"),
    ("材料加工", "特殊材料", "1C102", "特种合金", "7206,7506,7601,8101,8102,8103,8104,8105,8106,8107,8108,8109,8110,8111", "严格管控", 1, "钛合金、高温合金等"),
    ("材料加工", "特殊材料", "1C103", "特种陶瓷", "6901,6903", "严格管控", 1, "用于高温结构件"),
    ("材料加工", "特殊材料", "1C104", "特种金属", "2804,2805,7401,7501,7506,7601,8101,8102,8103,8104,8105,8106,8107,8108,8109,8110,8111", "严格管控", 1, "铍、铊等特种金属"),
    ("材料加工", "特殊材料", "1C105", "特种复合材料", "3926,6815", "严格管控", 1, "碳/碳复合材料"),
    ("材料加工", "特殊材料", "1C106", "特种润滑材料", "3824", "严格管控", 1, "用于航天和导弹"),
    ("材料加工", "特殊材料", "1C107", "特种纤维材料", "5401,5402,5403,5404,5405,5406,5407,5408,5501,5502,5503,5504,5505,5506,5507,5508,5509,5510,5511,5512,5513,5514,5515,5516", "严格管控", 1, "芳纶纤维、超高分子量聚乙烯纤维"),
    ("材料加工", "特殊材料", "1C108", "特种金属粉末", "7206,7506,7601,8101,8102,8103,8104,8105,8106,8107,8108,8109,8110,8111", "严格管控", 1, "用于增材制造和喷涂"),
    ("材料加工", "特殊材料", "1C109", "特种磁体材料", "8505", "严格管控", 1, "稀土永磁材料"),
    ("材料加工", "特殊材料", "1C110", "特种光学材料", "9001,9002", "严格管控", 1, "用于激光和光学系统"),
    ("材料加工", "特殊材料", "1C111", "特种超导材料", "8504", "严格管控", 1, "高温超导材料"),
    ("材料加工", "特殊材料", "1C112", "特种半导体材料", "2804,2841,2843,2846,2847,3824,8541,8542", "严格管控", 1, "砷化镓、氮化镓等"),
    ("材料加工", "特殊材料", "1C113", "特种碳材料", "2803,3801,6901,6902,6903", "严格管控", 1, "石墨、石墨烯"),
    ("材料加工", "特殊材料", "1C114", "特种稀土材料", "2804,2846", "严格管控", 1, "稀土金属及化合物"),
    ("材料加工", "特殊材料", "1C115", "特种高分子材料", "3901,3902,3903,3904,3905,3906,3907,3908,3909,3910,3911", "严格管控", 1, "聚酰亚胺、聚苯并咪唑等"),
    ("材料加工", "特殊材料", "1C116", "特种纳米材料", "2818,2846,3801,6901,6902,6903", "严格管控", 1, "纳米级特种材料"),
    ("材料加工", "特殊材料", "1C117", "特种含能材料", "3601,3602,3603,3604", "严格管控", 1, "推进剂、炸药前体"),
    ("材料加工", "特殊材料", "1C118", "特种防热材料", "3926,6815,6901,6903", "严格管控", 1, "用于航天器热防护"),
    ("材料加工", "特殊材料", "1C119", "特种隐身材料", "3926,6815,8421", "严格管控", 1, "雷达吸波材料"),
    ("材料加工", "特殊材料", "1C120", "特种核材料", "2844,2845", "严格管控", 1, "铀、钚、钍等"),
    ("材料加工", "特殊材料", "1C121", "特种同位素", "2844,2845", "严格管控", 1, "氚、氦-3等"),
    ("材料加工", "特殊材料", "1C122", "特种重水", "2845", "严格管控", 1, "用于核反应堆"),
    ("材料加工", "特殊材料", "1C123", "特种石墨", "3801,6801,6802,6901,6902,6903", "严格管控", 1, "核级石墨"),
    ("材料加工", "特殊材料", "1C124", "特种锆材料", "8109", "严格管控", 1, "核级锆"),
    ("材料加工", "特殊材料", "1C125", "特种锂材料", "8106", "严格管控", 1, "锂-6等"),
    ("材料加工", "特殊材料", "1C126", "特种铍材料", "8102", "严格管控", 1, "核级铍"),
    ("材料加工", "特殊材料", "1C127", "特种硼材料", "2810", "严格管控", 1, "硼-10等"),
    ("材料加工", "特殊材料", "1C128", "特种钨材料", "8101", "严格管控", 1, "钨合金"),
    ("材料加工", "特殊材料", "1C129", "特种钼材料", "8102", "严格管控", 1, "钼合金"),
    ("材料加工", "特殊材料", "1C130", "特种铼材料", "8106", "严格管控", 1, "铼合金"),
    ("材料加工", "特殊材料", "1C131", "特种铌材料", "8110", "严格管控", 1, "铌合金"),
    ("材料加工", "特殊材料", "1C132", "特种钽材料", "8110", "严格管控", 1, "钽合金"),
    ("材料加工", "特殊材料", "1C133", "特种铬材料", "8111", "严格管控", 1, "高纯铬"),
    ("材料加工", "特殊材料", "1C134", "特种钒材料", "8109", "严格管控", 1, "钒合金"),
    ("材料加工", "特殊材料", "1C135", "特种钛材料", "8108", "严格管控", 1, "钛合金"),
    ("材料加工", "特殊材料", "1C136", "特种镍材料", "7506", "严格管控", 1, "高温镍合金"),
    ("材料加工", "特殊材料", "1C137", "特种钴材料", "8105", "严格管控", 1, "钴合金"),
    ("材料加工", "特殊材料", "1C138", "特种锰材料", "8111", "严格管控", 1, "高纯锰"),
    ("材料加工", "特殊材料", "1C139", "特种锑材料", "8110", "严格管控", 1, "高纯锑"),
    ("材料加工", "特殊材料", "1C140", "特种铋材料", "8110", "严格管控", 1, "高纯铋"),
    ("材料加工", "特殊材料", "1C141", "特种镓材料", "8110", "严格管控", 1, "高纯镓"),
    ("材料加工", "特殊材料", "1C142", "特种铟材料", "8110", "严格管控", 1, "高纯铟"),
    ("材料加工", "特殊材料", "1C143", "特种锗材料", "8110", "严格管控", 1, "高纯锗"),
    ("材料加工", "特殊材料", "1C144", "特种硒材料", "8110", "严格管控", 1, "高纯硒"),
    ("材料加工", "特殊材料", "1C145", "特种碲材料", "8110", "严格管控", 1, "高纯碲"),
    ("材料加工", "特殊材料", "1C146", "特种铪材料", "8110", "严格管控", 1, "高纯铪"),
    ("材料加工", "特殊材料", "1C147", "特种钪材料", "8110", "严格管控", 1, "高纯钪"),
    ("材料加工", "特殊材料", "1C148", "特种钇材料", "8110", "严格管控", 1, "高纯钇"),
    ("材料加工", "特殊材料", "1C149", "特种铽材料", "8110", "严格管控", 1, "高纯铽"),
    ("材料加工", "特殊材料", "1C150", "特种镝材料", "8110", "严格管控", 1, "高纯镝"),
    ("材料加工", "特殊材料", "1C151", "特种钕材料", "8110", "严格管控", 1, "高纯钕"),
    ("材料加工", "特殊材料", "1C152", "特种镨材料", "8110", "严格管控", 1, "高纯镨"),
    ("材料加工", "特殊材料", "1C153", "特种铕材料", "8110", "严格管控", 1, "高纯铕"),
    ("材料加工", "特殊材料", "1C154", "特种钐材料", "8110", "严格管控", 1, "高纯钐"),
    ("材料加工", "特殊材料", "1C155", "特种钆材料", "8110", "严格管控", 1, "高纯钆"),
    ("材料加工", "特殊材料", "1C156", "特种铒材料", "8110", "严格管控", 1, "高纯铒"),
    ("材料加工", "特殊材料", "1C157", "特种镥材料", "8110", "严格管控", 1, "高纯镥"),
    ("材料加工", "特殊材料", "1C158", "特种钬材料", "8110", "严格管控", 1, "高纯钬"),
    ("材料加工", "特殊材料", "1C159", "特种铥材料", "8110", "严格管控", 1, "高纯铥"),
    ("材料加工", "特殊材料", "1C160", "特种镱材料", "8110", "严格管控", 1, "高纯镱"),
    ("材料加工", "特殊材料", "1C161", "特种铈材料", "8110", "严格管控", 1, "高纯铈"),
    ("材料加工", "特殊材料", "1C162", "特种镧材料", "8110", "严格管控", 1, "高纯镧"),
    ("材料加工", "特殊材料", "1C163", "特种钷材料", "8110", "严格管控", 1, "高纯钷"),
    ("电子", "电子设备", "1D001", "高性能计算机", "8471", "严格管控", 1, "超过一定计算性能的计算机"),
    ("电子", "电子设备", "1D002", "数字计算机及相关设备", "8471,847150", "严格管控", 1, "具有特定功能的数字计算机"),
    ("电子", "电子设备", "1D003", "电子设备", "8541,8542", "严格管控", 1, "具有特定功能的电子设备"),
    ("电子", "电子设备", "1D004", "混合计算机", "8471", "严格管控", 1, "模拟/数字混合计算机"),
    ("电子", "电子设备", "1D005", "信号处理设备", "8542,8543", "严格管控", 1, "高性能信号处理设备"),
    ("电子", "电子设备", "1D006", "数据记录设备", "8523", "严格管控", 1, "高速数据记录设备"),
    ("电子", "电子设备", "1D007", "通信设备", "8517", "严格管控", 1, "具有加密功能的通信设备"),
    ("电子", "电子设备", "1D008", "网络监控设备", "8517,8543", "严格管控", 1, "网络监控和分析设备"),
    ("电子", "电子设备", "1D009", "量子计算机", "8471", "严格管控", 1, "量子计算设备"),
    ("电子", "电子设备", "1D010", "AI加速器", "8471,8542", "严格管控", 1, "高性能AI计算加速器"),
    ("电子", "电子设备", "1D011", "电磁脉冲(EMP)设备", "8543", "严格管控", 1, "电磁脉冲发生设备"),
    ("电子", "电子设备", "1D012", "电子对抗设备", "8525,8543", "严格管控", 1, "电子战设备"),
    ("电子", "电子设备", "1D013", "密码设备", "8542", "严格管控", 1, "加密和解密设备"),
    ("电子", "电子设备", "1D014", "信号情报设备", "8525,8543", "严格管控", 1, "信号截获和分析设备"),
    ("电子", "电子设备", "1D015", "导航干扰设备", "8525,8543", "严格管控", 1, "GPS/GNSS干扰设备"),
    ("电子", "电子设备", "1D016", "高性能示波器", "9030", "严格管控", 1, "超宽带示波器"),
    ("电子", "电子设备", "1D017", "频谱分析仪", "9030", "严格管控", 1, "高性能频谱分析仪"),
    ("电子", "电子设备", "1D018", "网络测试设备", "9031", "严格管控", 1, "网络渗透测试设备"),
    ("电子", "电子设备", "1D019", "高性能ADC/DAC", "8542", "严格管控", 1, "超高速模数/数模转换器"),
    ("电子", "电子设备", "1D020", "微波器件", "8541,8542", "严格管控", 1, "高功率微波器件"),
    ("电子", "电子设备", "1D021", "红外探测器", "9013,8541", "严格管控", 1, "高性能红外探测器件"),
    ("电子", "电子设备", "1D022", "激光器", "9013,8525", "严格管控", 1, "高功率激光器"),
    ("电子", "电子设备", "1D023", "声学设备", "8518,8543", "严格管控", 1, "高性能声学探测设备"),
    ("电子", "电子设备", "1D024", "雷达设备", "8525", "严格管控", 1, "高性能雷达设备"),
    ("电子", "电子设备", "1D025", "卫星通信设备", "8517,8525", "严格管控", 1, "卫星通信地面站设备"),
    ("电子", "电子设备", "1D026", "光纤通信设备", "8517,9001", "严格管控", 1, "高性能光纤通信设备"),
    ("电子", "电子设备", "1D027", "无线电设备", "8517,8525", "严格管控", 1, "高性能无线电设备"),
    ("电子", "电子设备", "1D028", "电子测量设备", "9030,9031", "严格管控", 1, "高精度电子测量设备"),
    ("电子", "电子设备", "1D029", "传感器", "9025,9026,9031", "严格管控", 1, "高性能传感器"),
    ("计算机", "计算机设备", "2A001", "数字计算机", "8471", "严格管控", 1, "超过一定性能的数字计算机"),
    ("计算机", "计算机设备", "2A002", "混合计算机", "8471", "严格管控", 1, "模拟/数字混合计算机"),
    ("计算机", "计算机设备", "2A003", "数据处理设备", "8471", "严格管控", 1, "具有特定数据处理能力的设备"),
    ("计算机", "计算机设备", "2A004", "存储设备", "847170,8523", "严格管控", 1, "高性能存储设备"),
    ("计算机", "计算机设备", "2A005", "网络设备", "8517", "严格管控", 1, "高性能网络设备"),
    ("计算机", "计算机设备", "2A006", "显示设备", "8528", "严格管控", 1, "高性能显示设备"),
    ("计算机", "计算机设备", "2A007", "打印设备", "8443", "严格管控", 1, "高性能打印设备"),
    ("计算机", "计算机设备", "2A008", "输入设备", "8471", "严格管控", 1, "高性能输入设备"),
    ("计算机", "计算机设备", "2A009", "输出设备", "8471", "严格管控", 1, "高性能输出设备"),
    ("计算机", "计算机设备", "2A010", "服务器", "8471", "严格管控", 1, "高性能服务器"),
    ("计算机", "计算机设备", "2A011", "工作站", "8471", "严格管控", 1, "高性能工作站"),
    ("计算机", "计算机设备", "2A012", "嵌入式系统", "8471,8542", "严格管控", 1, "高性能嵌入式系统"),
    ("计算机", "计算机设备", "2A013", "云计算设备", "8471", "严格管控", 1, "云计算基础设施设备"),
    ("计算机", "计算机设备", "2A014", "边缘计算设备", "8471,8542", "严格管控", 1, "边缘计算设备"),
    ("计算机", "计算机设备", "2A015", "AI训练设备", "8471,8542", "严格管控", 1, "AI模型训练专用设备"),
    ("计算机", "计算机设备", "2A016", "量子计算设备", "8471", "严格管控", 1, "量子计算设备"),
    ("计算机", "计算机设备", "2A017", "区块链设备", "8471,8542", "严格管控", 1, "区块链专用计算设备"),
    ("计算机", "计算机设备", "2A018", "生物计算设备", "8471", "严格管控", 1, "生物计算设备"),
    ("计算机", "计算机设备", "2A019", "光子计算设备", "8471", "严格管控", 1, "光子计算设备"),
    ("计算机", "计算机设备", "2A020", "神经形态计算设备", "8471,8542", "严格管控", 1, "神经形态计算设备"),
    ("电信和信息安全", "通信设备", "5A001", "电信设备", "8517", "严格管控", 1, "高性能电信设备"),
    ("电信和信息安全", "通信设备", "5A002", "加密设备", "8542", "严格管控", 1, "加密通信设备"),
    ("电信和信息安全", "通信设备", "5A003", "信息分析设备", "8471,8543", "严格管控", 1, "信息安全和分析设备"),
    ("电信和信息安全", "通信设备", "5A004", "网络监控设备", "8517,8543", "严格管控", 1, "网络监控设备"),
    ("电信和信息安全", "通信设备", "5A005", "信号处理设备", "8542,8543", "严格管控", 1, "高性能信号处理设备"),
    ("电信和信息安全", "通信设备", "5A006", "无线电设备", "8517,8525", "严格管控", 1, "高性能无线电设备"),
    ("电信和信息安全", "通信设备", "5A007", "卫星通信设备", "8517,8525", "严格管控", 1, "卫星通信设备"),
    ("电信和信息安全", "通信设备", "5A008", "光纤通信设备", "8517,9001", "严格管控", 1, "高性能光纤通信设备"),
    ("电信和信息安全", "通信设备", "5A009", "密码设备", "8542", "严格管控", 1, "加密和解密设备"),
    ("电信和信息安全", "通信设备", "5A010", "电子对抗设备", "8525,8543", "严格管控", 1, "电子战设备"),
    ("电信和信息安全", "通信设备", "5A011", "导航干扰设备", "8525,8543", "严格管控", 1, "GPS/GNSS干扰设备"),
    ("电信和信息安全", "通信设备", "5A012", "电磁脉冲设备", "8543", "严格管控", 1, "电磁脉冲发生设备"),
    ("传感器和激光器", "传感器", "6A001", "加速度传感器", "9031", "严格管控", 1, "高精度加速度传感器"),
    ("传感器和激光器", "传感器", "6A002", "陀螺仪", "9014,9031", "严格管控", 1, "高精度陀螺仪"),
    ("传感器和激光器", "传感器", "6A003", "激光器", "9013", "严格管控", 1, "高功率激光器"),
    ("传感器和激光器", "传感器", "6A004", "红外探测器", "9013", "严格管控", 1, "高性能红外探测器"),
    ("传感器和激光器", "传感器", "6A005", "声学传感器", "9014,9031", "严格管控", 1, "高性能声学传感器"),
    ("传感器和激光器", "传感器", "6A006", "磁传感器", "9031", "严格管控", 1, "高精度磁传感器"),
    ("传感器和激光器", "传感器", "6A007", "压力传感器", "9031", "严格管控", 1, "高精度压力传感器"),
    ("传感器和激光器", "传感器", "6A008", "温度传感器", "9025", "严格管控", 1, "高精度温度传感器"),
    ("传感器和激光器", "传感器", "6A009", "化学传感器", "9027", "严格管控", 1, "高性能化学传感器"),
    ("传感器和激光器", "传感器", "6A010", "生物传感器", "9027", "严格管控", 1, "高性能生物传感器"),
    ("传感器和激光器", "传感器", "6A011", "辐射传感器", "9030", "严格管控", 1, "高性能辐射传感器"),
    ("传感器和激光器", "传感器", "6A012", "光学传感器", "9031", "严格管控", 1, "高性能光学传感器"),
    ("传感器和激光器", "传感器", "6A013", "图像传感器", "8525", "严格管控", 1, "高性能图像传感器"),
    ("传感器和激光器", "传感器", "6A014", "雷达传感器", "8525", "严格管控", 1, "高性能雷达传感器"),
    ("传感器和激光器", "传感器", "6A015", "地震传感器", "9031", "严格管控", 1, "高性能地震传感器"),
    ("导航和航空电子", "导航设备", "7A001", "惯性导航系统", "9014", "严格管控", 1, "高精度惯性导航系统"),
    ("导航和航空电子", "导航设备", "7A002", "卫星导航设备", "8517,8525", "严格管控", 1, "高精度卫星导航设备"),
    ("导航和航空电子", "导航设备", "7A003", "航空电子设备", "9014", "严格管控", 1, "航空电子设备"),
    ("导航和航空电子", "导航设备", "7A004", "飞行控制系统", "9014", "严格管控", 1, "飞行控制系统"),
    ("导航和航空电子", "导航设备", "7A005", "雷达高度计", "8525", "严格管控", 1, "雷达高度计"),
    ("导航和航空电子", "导航设备", "7A006", "自动驾驶仪", "9014", "严格管控", 1, "自动驾驶仪"),
    ("导航和航空电子", "导航设备", "7A007", "电子战设备", "8525,8543", "严格管控", 1, "航空电子战设备"),
    ("导航和航空电子", "导航设备", "7A008", "通信导航设备", "8517,9014", "严格管控", 1, "通信导航一体化设备"),
    ("导航和航空电子", "导航设备", "7A009", "合成孔径雷达", "8525", "严格管控", 1, "合成孔径雷达"),
    ("导航和航空电子", "导航设备", "7A010", "地形跟随雷达", "8525", "严格管控", 1, "地形跟随雷达"),
    ("导航和航空电子", "导航设备", "7A011", "电子对抗设备", "8525,8543", "严格管控", 1, "航空电子对抗设备"),
    ("导航和航空电子", "导航设备", "7A012", "光电瞄准系统", "9013", "严格管控", 1, "光电瞄准系统"),
    ("导航和航空电子", "导航设备", "7A013", "头盔显示系统", "9013", "严格管控", 1, "头盔显示系统"),
    ("导航和航空电子", "导航设备", "7A014", "数据链设备", "8517", "严格管控", 1, "航空数据链设备"),
    ("导航和航空电子", "导航设备", "7A015", "无人机控制系统", "8802,9014", "严格管控", 1, "无人机飞控系统"),
    ("船舶", "船舶设备", "8A001", "潜艇及潜水器", "8906", "严格管控", 1, "军用潜艇及潜水器"),
    ("船舶", "船舶设备", "8A002", "水面舰艇", "8906", "严格管控", 1, "军用水面舰艇"),
    ("船舶", "船舶设备", "8A003", "船舶推进系统", "8408,8483", "严格管控", 1, "高性能船舶推进系统"),
    ("船舶", "船舶设备", "8A004", "声纳系统", "8525", "严格管控", 1, "舰载声纳系统"),
    ("船舶", "船舶设备", "8A005", "船舶导航设备", "9014", "严格管控", 1, "高性能船舶导航设备"),
    ("船舶", "船舶设备", "8A006", "水下探测设备", "8525,9014", "严格管控", 1, "水下探测设备"),
    ("船舶", "船舶设备", "8A007", "船舶通信设备", "8517", "严格管控", 1, "舰载通信设备"),
    ("船舶", "船舶设备", "8A008", "消磁系统", "8543", "严格管控", 1, "舰船消磁系统"),
    ("船舶", "船舶设备", "8A009", "鱼雷发射系统", "9301", "严格管控", 1, "鱼雷发射系统"),
    ("船舶", "船舶设备", "8A010", "水雷", "9301,9302", "严格管控", 1, "水雷及反水雷设备"),
    ("航空航天与推进", "航空航天", "9A001", "军用飞机", "8802", "严格管控", 1, "军用飞机及零部件"),
    ("航空航天与推进", "航空航天", "9A002", "军用直升机", "8802", "严格管控", 1, "军用直升机及零部件"),
    ("航空航天与推进", "航空航天", "9A003", "无人机", "8802", "严格管控", 1, "军用无人机"),
    ("航空航天与推进", "航空航天", "9A004", "航空发动机", "8411", "严格管控", 1, "高性能航空发动机"),
    ("航空航天与推进", "航空航天", "9A005", "火箭发动机", "8412", "严格管控", 1, "火箭发动机"),
    ("航空航天与推进", "航空航天", "9A006", "航天器", "8802", "严格管控", 1, "航天器及零部件"),
    ("航空航天与推进", "航空航天", "9A007", "导弹", "9301", "严格管控", 1, "导弹及零部件"),
    ("航空航天与推进", "航空航天", "9A008", "航空电子设备", "9014", "严格管控", 1, "航空电子设备"),
    ("航空航天与推进", "航空航天", "9A009", "飞行控制系统", "9014", "严格管控", 1, "飞行控制系统"),
    ("航空航天与推进", "航空航天", "9A010", "航空仪表", "9014,9015", "严格管控", 1, "航空仪表"),
    ("航空航天与推进", "航空航天", "9A011", "航空液压系统", "8412", "严格管控", 1, "航空液压系统"),
    ("航空航天与推进", "航空航天", "9A012", "航空燃油系统", "8413", "严格管控", 1, "航空燃油系统"),
    ("航空航天与推进", "航空航天", "9A013", "航空氧气系统", "9020", "严格管控", 1, "航空氧气系统"),
    ("航空航天与推进", "航空航天", "9A014", "弹射座椅", "9401", "严格管控", 1, "弹射座椅"),
    ("航空航天与推进", "航空航天", "9A015", "航空雷达", "8525", "严格管控", 1, "航空雷达"),
    ("航空航天与推进", "航空航天", "9A016", "航空通信设备", "8517", "严格管控", 1, "航空通信设备"),
    ("航空航天与推进", "航空航天", "9A017", "航空导航设备", "9014", "严格管控", 1, "航空导航设备"),
    ("航空航天与推进", "航空航天", "9A018", "航空电子战设备", "8525,8543", "严格管控", 1, "航空电子战设备"),
    ("航空航天与推进", "航空航天", "9A019", "航空武器系统", "9301", "严格管控", 1, "航空武器系统"),
    ("航空航天与推进", "航空航天", "9A020", "航空训练模拟器", "9023", "严格管控", 1, "航空训练模拟器"),
    ("航空航天与推进", "航空航天", "9A021", "航空测试设备", "9031", "严格管控", 1, "航空测试设备"),
    ("航空航天与推进", "航空航天", "9A022", "航空零部件", "8803", "严格管控", 1, "航空专用零部件"),
    ("航空航天与推进", "航空航天", "9A023", "航天推进系统", "8412", "严格管控", 1, "航天推进系统"),
    ("航空航天与推进", "航空航天", "9A024", "航天热防护系统", "3926,6815", "严格管控", 1, "航天热防护系统"),
    ("航空航天与推进", "航空航天", "9A025", "航天结构部件", "8803", "严格管控", 1, "航天结构部件"),
    ("航空航天与推进", "航空航天", "9A026", "航天电子设备", "8542", "严格管控", 1, "航天电子设备"),
    ("航空航天与推进", "航空航天", "9A027", "航天通信设备", "8517", "严格管控", 1, "航天通信设备"),
    ("航空航天与推进", "航空航天", "9A028", "航天导航设备", "9014", "严格管控", 1, "航天导航设备"),
    ("航空航天与推进", "航空航天", "9A029", "航天遥测设备", "8525", "严格管控", 1, "航天遥测设备"),
    ("航空航天与推进", "航空航天", "9A030", "航天控制系统", "9032", "严格管控", 1, "航天控制系统"),
    ("航空航天与推进", "航空航天", "9A031", "航天传感器", "9031", "严格管控", 1, "航天传感器"),
    ("航空航天与推进", "航空航天", "9A032", "航天光学设备", "9001,9002", "严格管控", 1, "航天光学设备"),
    ("航空航天与推进", "航空航天", "9A033", "航天热控设备", "8419", "严格管控", 1, "航天热控设备"),
    ("航空航天与推进", "航空航天", "9A034", "航天电源系统", "8504,8507", "严格管控", 1, "航天电源系统"),
    ("航空航天与推进", "航空航天", "9A035", "航天生命保障系统", "9018,9020", "严格管控", 1, "航天生命保障系统"),
    ("航空航天与推进", "航空航天", "9A036", "航天返回舱", "8802", "严格管控", 1, "航天返回舱"),
    ("航空航天与推进", "航空航天", "9A037", "航天对接机构", "8803", "严格管控", 1, "航天对接机构"),
    ("航空航天与推进", "航空航天", "9A038", "航天太阳翼", "8507,8541", "严格管控", 1, "航天太阳翼"),
    ("航空航天与推进", "航空航天", "9A039", "航天天线", "8517", "严格管控", 1, "航天天线"),
    ("航空航天与推进", "航空航天", "9A040", "航天推进剂", "3601,3602", "严格管控", 1, "航天推进剂"),
    ("航空航天与推进", "航空航天", "9A041", "航天特种材料", "3926,6815", "严格管控", 1, "航天特种材料"),
    ("航空航天与推进", "航空航天", "9A042", "航天紧固件", "7318", "严格管控", 1, "航天特种紧固件"),
    ("航空航天与推进", "航空航天", "9A043", "航天密封件", "4016", "严格管控", 1, "航天密封件"),
    ("航空航天与推进", "航空航天", "9A044", "航天轴承", "8482", "严格管控", 1, "航天轴承"),
    ("航空航天与推进", "航空航天", "9A045", "航天齿轮", "8483", "严格管控", 1, "航天齿轮"),
    ("航空航天与推进", "航空航天", "9A046", "航天阀门", "8481", "严格管控", 1, "航天阀门"),
    ("航空航天与推进", "航空航天", "9A047", "航天管路", "7304", "严格管控", 1, "航天管路"),
    ("航空航天与推进", "航空航天", "9A048", "航天电气连接器", "8536", "严格管控", 1, "航天电气连接器"),
    ("航空航天与推进", "航空航天", "9A049", "航天电缆", "8544", "严格管控", 1, "航天电缆"),
    ("航空航天与推进", "航空航天", "9A050", "航天继电器", "8536", "严格管控", 1, "航天继电器"),
    ("其他物项", "其他", "0A001", "未分类两用物项", "", "严格管控", 1, "其他两用物项"),
]


def init_hs_data():
    """初始化HS编码数据"""
    with get_db_context() as conn:
        cursor = conn.cursor()

        # 插入WCO HS大类（2位编码）
        for code, level, desc_cn, desc_en in WCO_HS_CHAPTERS:
            try:
                cursor.execute('''
                    INSERT OR IGNORE INTO hs_codes (code, code_level, description_cn, description_en, source, parent_code)
                    VALUES (?, ?, ?, ?, 'WCO', NULL)
                ''', (code, level, desc_cn, desc_en))
            except Exception as e:
                print(f"⚠️ 插入WCO编码 {code} 失败: {e}")

        # 插入常用HS编码（4位和6位）
        for item in COMMON_HS_CODES:
            code = item[0]
            level = item[1]
            desc_cn = item[2]
            desc_en = item[3]
            unit = item[4]
            tax_import = item[5]
            vat = item[6]
            rebate = item[7]
            supervision = item[8]
            keywords = item[9]

            # 确定父编码
            parent_code = code[:2] if level == 4 else code[:4]

            try:
                cursor.execute('''
                    INSERT OR IGNORE INTO hs_codes
                    (code, code_level, description_cn, description_en, source, parent_code,
                     unit, tax_rate_import, vat_rate, export_rebate_rate, customs_supervision, search_keywords)
                    VALUES (?, ?, ?, ?, 'CN_CUSTOMS', ?, ?, ?, ?, ?, ?, ?)
                ''', (code, level, desc_cn, desc_en, parent_code,
                      unit, tax_import, vat, rebate, supervision, keywords))
            except Exception as e:
                print(f"⚠️ 插入编码 {code} 失败: {e}")

        # 插入8位本国子目编码
        for item in CN_8DIGIT_CODES:
            code = item[0]
            level = item[1]
            desc_cn = item[2]
            desc_en = item[3]
            unit = item[4]
            tax_import = item[5]
            vat = item[6]
            rebate = item[7]
            supervision = item[8]
            keywords = item[9]
            parent_code = code[:6]
            try:
                cursor.execute('''
                    INSERT OR IGNORE INTO hs_codes
                    (code, code_level, description_cn, description_en, source, parent_code,
                     unit, tax_rate_import, vat_rate, export_rebate_rate, customs_supervision, search_keywords)
                    VALUES (?, ?, ?, ?, 'CN_CUSTOMS', ?, ?, ?, ?, ?, ?, ?)
                ''', (code, level, desc_cn, desc_en, parent_code,
                      unit, tax_import, vat, rebate, supervision, keywords))
            except Exception as e:
                print(f"⚠️ 插入8位编码 {code} 失败: {e}")

        # 插入10位完整海关编码
        for item in CN_10DIGIT_CODES:
            code = item[0]
            level = item[1]
            desc_cn = item[2]
            desc_en = item[3]
            unit = item[4]
            tax_import = item[5]
            vat = item[6]
            rebate = item[7]
            supervision = item[8]
            keywords = item[9]
            parent_code = code[:8]
            try:
                cursor.execute('''
                    INSERT OR IGNORE INTO hs_codes
                    (code, code_level, description_cn, description_en, source, parent_code,
                     unit, tax_rate_import, vat_rate, export_rebate_rate, customs_supervision, search_keywords)
                    VALUES (?, ?, ?, ?, 'CN_CUSTOMS', ?, ?, ?, ?, ?, ?, ?)
                ''', (code, level, desc_cn, desc_en, parent_code,
                      unit, tax_import, vat, rebate, supervision, keywords))
            except Exception as e:
                print(f"⚠️ 插入10位编码 {code} 失败: {e}")

        # 插入两用物项清单
        for item in DUAL_USE_ITEMS:
            category = item[0]
            subcategory = item[1]
            item_code = item[2]
            description = item[3]
            hs_codes = item[4]
            control_level = item[5]
            license_required = item[6]
            notes = item[7]

            try:
                cursor.execute('''
                    INSERT OR IGNORE INTO dual_use_items
                    (category, subcategory, item_code, description, hs_codes,
                     control_level, license_required, notes, source, effective_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'MOFCOM_2024', '2024-12-01')
                ''', (category, subcategory, item_code, description, hs_codes,
                      control_level, license_required, notes))
            except Exception as e:
                print(f"⚠️ 插入两用物项 {item_code} 失败: {e}")

        # 更新HS编码的两用物项标记
        # 获取所有两用物项中涉及的HS编码前缀
        cursor.execute('SELECT DISTINCT hs_codes FROM dual_use_items WHERE hs_codes != ""')
        dual_use_hs_prefixes = set()
        for row in cursor.fetchall():
            codes_str = row[0]
            for code in codes_str.split(','):
                code = code.strip()
                if code and len(code) >= 2:
                    dual_use_hs_prefixes.add(code[:2])
                    if len(code) >= 4:
                        dual_use_hs_prefixes.add(code[:4])

        # 更新匹配的HS编码
        for prefix in dual_use_hs_prefixes:
            cursor.execute('''
                UPDATE hs_codes
                SET is_dual_use = 1,
                    dual_use_category = (
                        SELECT GROUP_CONCAT(di.category, '; ')
                        FROM (SELECT DISTINCT category FROM dual_use_items WHERE hs_codes LIKE ?) di
                    )
                WHERE code LIKE ? AND is_dual_use = 0
            ''', (f"%{prefix}%", f"{prefix}%"))

        # 统计数据
        cursor.execute("SELECT COUNT(*) FROM hs_codes WHERE source='WCO'")
        wco_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM hs_codes WHERE source='CN_CUSTOMS'")
        cn_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM dual_use_items")
        dual_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM hs_codes WHERE is_dual_use=1")
        dual_hs_count = cursor.fetchone()[0]

        print(f"\n{'='*50}")
        print(f"✅ HS编码数据初始化完成")
        print(f"{'='*50}")
        print(f"  WCO国际编码（2位）: {wco_count} 条")
        print(f"  中国海关编码（4/6位）: {cn_count} 条")
        print(f"  两用物项清单: {dual_count} 条")
        print(f"  标记为两用物项的HS编码: {dual_hs_count} 条")
        print(f"  总计HS编码: {wco_count + cn_count} 条")
        print(f"{'='*50}")


if __name__ == '__main__':
    init_hs_data()
