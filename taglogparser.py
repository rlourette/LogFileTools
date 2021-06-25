import datetime
import getopt
import hashlib
import re
import sys
from enum import Enum
from os.path import splitext
from time import strptime
from zipfile import ZipFile
import ctypes
from sortedcontainers import SortedDict
from statistics import mean, pstdev
# (?P<time>[0-9]{4}-[0-9]{2}-[0-9]{2}\s[0-9]{2}:[0-9]{2}:[0-9]{2}).*TagCmdContext\((?P<uuid>[A-F0-9]{16}).*Multiple\((?P<fielddata>.*)\)
# TemplateDataRegex = r'.*TagCmdContext\(([A-F0-9]{16}).*Multiple\((.*)\)'
TemplateDataRegex = r'(?P<time>[0-9]{4}-[0-9]{2}-[0-9]{2}\s[0-9]{2}:[0-9]{2}:[0-9]{2}).*TagCmdContext\((?P<uuid>[A-F0-9]{16}).*Multiple\((?P<fielddata>.*)\)'
TemplateDataRegexCompiled = re.compile(TemplateDataRegex)

#(?P<time>[0-9]{4}-[0-9]{2}-[0-9]{2}\s[0-9]{2}:[0-9]{2}:[0-9]{2}).*Multiple\(TemplateData:\s\[(?P<fieldtype>Text)\sDataIndex:(?P<dataidx>[0-9]+)\sFldNum:(?P<fieldnum>[0-9]+)\sData:\'(?P<data>[-\ \w]*)\'
FieldRegex = r'TemplateData:\s\[(?P<fieldtype>Text)\sDataIndex:(?P<dataidx>[0-9]+)\sFldNum:(?P<fieldnum>[0-9]+)\sData:\'(?P<data>[-\ \w]*)\''
FieldRegexCompiled = re.compile(FieldRegex)

FieldDataBlankCompiled = re.compile('^\s+$')

# (success False)|(Gateway\(10.16.220.[0-9]{3}\) Exception\|System.Net.WebException: The operation has timed out)

# 2021-06-02 10:27:05.9496|INFO|Panasonic.Hdk.Gateway.Internal.CmdDispatcher|137|WhiteListPrepared: New Cmd: TagUID: 'D9AE160000003171' Gtwy:Gateway(10.16.220.210) Rdr:-- [CID1235079] AwaitTrigger[XmitAttmpt8] [76,843ms] TagID: D9AE160000003171|
# 2021-06-02 10:27:09.2210|INFO|Panasonic.Hdk.Gateway.Internal.CmdDispatcher|119|executeSendingTagCmd(): => Sending Cmd: [CID1235079] Sending[XmitAttmpt9] TagUID: 'D9AE160000003171' Gtwy:Gateway(10.16.220.210) Rdr:--|
# 2021-06-02 10:27:11.9714|INFO|Panasonic.Hdk.Context.TagContextMgr|40|ContextCompleted TagCmdGrpContext(D9AE160000003171) - [CGID323647 Timeout 17secs] success False|

trimandfoamgateways = [
    '10.16.220.210',
    '10.16.220.211',
    '10.16.220.212',
    '10.16.220.213',
]

trimandfoamtags = [
"D9AE1500000003A5",
"D9AE150000000745",
"D9AE1500000008D0",
"D9AE150000001312",
"D9AE150000001342",
"D9AE150000001356",
"D9AE15000000135A",
"D9AE150000001361",
"D9AE150000001569",
"D9AE150000001583",
"D9AE1500000015BB",
"D9AE1500000015BE",
"D9AE1500000015E4",
"D9AE1500000015F9",
"D9AE1500000015FD",
"D9AE150000001603",
"D9AE15000000162D",
"D9AE15000000171E",
"D9AE15000000172A",
"D9AE15000000173F",
"D9AE150000001748",
"D9AE150000001761",
"D9AE15000000176D",
"D9AE150000001795",
"D9AE1500000017AF",
"D9AE1500000017B0",
"D9AE15000000181F",
"D9AE15000000183E",
"D9AE15000000185C",
"D9AE150000001867",
"D9AE150000001877",
"D9AE150000001908",
"D9AE150000002371",
"D9AE1500000023FE",
"D9AE150000002412",
"D9AE1500000024A4",
"D9AE15000000251E",
"D9AE150000002526",
"D9AE150000002549",
"D9AE150000002CA9",
"D9AE150000002CC0",
"D9AE150000002CE0",
"D9AE150000002CE5",
"D9AE150000002D9E",
"D9AE150000002E11",
"D9AE150000002E25",
"D9AE150000002E26",
"D9AE150000002E27",
"D9AE150000002E28",
"D9AE150000003A45",
"D9AE150000003A4C",
"D9AE150000003A4F",
"D9AE150000003A53",
"D9AE150000003A54",
"D9AE150000003A56",
"D9AE150000003A57",
"D9AE150000003A5E",
"D9AE150000003A5F",
"D9AE150000003A63",
"D9AE150000003A64",
"D9AE150000003AA3",
"D9AE150000003B5D",
"D9AE160000000156",
"D9AE16000000015E",
"D9AE16000000017D",
"D9AE160000000193",
"D9AE1600000001A1",
"D9AE1600000001EE",
"D9AE16000000021B",
"D9AE160000000250",
"D9AE160000000251",
"D9AE160000000260",
"D9AE160000000280",
"D9AE16000000041F",
"D9AE160000000497",
"D9AE1600000004ED",
"D9AE160000000515",
"D9AE160000000524",
"D9AE16000000052D",
"D9AE160000000534",
"D9AE160000000542",
"D9AE16000000054A",
"D9AE16000000055C",
"D9AE16000000056E",
"D9AE16000000057E",
"D9AE160000000598",
"D9AE160000000599",
"D9AE1600000005A7",
"D9AE1600000005AD",
"D9AE1600000005B2",
"D9AE1600000005E8",
"D9AE1600000005F0",
"D9AE1600000005FC",
"D9AE160000000635",
"D9AE16000000063E",
"D9AE160000000642",
"D9AE160000000649",
"D9AE16000000064A",
"D9AE160000001A42",
"D9AE160000001A70",
"D9AE160000001B48",
"D9AE160000001B4E",
"D9AE160000001B89",
"D9AE160000001C58",
"D9AE160000001D3D",
"D9AE160000001D6F",
"D9AE160000001D71",
"D9AE160000001D7D",
"D9AE160000001D88",
"D9AE160000001D9A",
"D9AE160000001D9B",
"D9AE160000001DC0",
"D9AE160000002351",
"D9AE160000002357",
"D9AE16000000235C",
"D9AE160000002363",
"D9AE16000000236E",
"D9AE160000002374",
"D9AE16000000237A",
"D9AE16000000237E",
"D9AE160000002384",
"D9AE1600000023AD",
"D9AE1600000023CE",
"D9AE1600000023F6",
"D9AE1600000023FC",
"D9AE160000002411",
"D9AE160000002481",
"D9AE16000000249D",
"D9AE1600000024C7",
"D9AE1600000024D6",
"D9AE1600000024D7",
"D9AE1600000024EE",
"D9AE160000002506",
"D9AE16000000250D",
"D9AE160000002510",
"D9AE160000002512",
"D9AE16000000251E",
"D9AE160000002520",
"D9AE16000000253C",
"D9AE160000002545",
"D9AE160000002559",
"D9AE160000002595",
"D9AE1600000025C8",
"D9AE1600000025E1",
"D9AE1600000026B0",
"D9AE1600000026CE",
"D9AE1600000026D2",
"D9AE1600000026E0",
"D9AE160000002730",
"D9AE1600000027C0",
"D9AE1600000027C1",
"D9AE1600000027C4",
"D9AE1600000027C6",
"D9AE1600000027C7",
"D9AE1600000027C8",
"D9AE1600000027C9",
"D9AE1600000027CA",
"D9AE1600000027CB",
"D9AE1600000027CD",
"D9AE1600000027D5",
"D9AE1600000027D7",
"D9AE1600000027DC",
"D9AE1600000027E0",
"D9AE1600000027E2",
"D9AE1600000027E3",
"D9AE1600000027E6",
"D9AE1600000027E7",
"D9AE1600000027E9",
"D9AE1600000027F0",
"D9AE1600000027F1",
"D9AE160000002808",
"D9AE16000000280C",
"D9AE160000002812",
"D9AE160000003158",
"D9AE16000000315B",
"D9AE16000000315D",
"D9AE16000000315F",
"D9AE160000003162",
"D9AE160000003169",
"D9AE16000000316A",
"D9AE160000003172",
"D9AE160000003176",
"D9AE16000000317F",
"D9AE160000003185",
"D9AE16000000318B",
"D9AE16000000318C",
"D9AE1600000031A1",
"D9AE1600000031A3",
"D9AE1600000031A6",
"D9AE1600000031B8",
"D9AE1600000031B9",
"D9AE1600000031BF",
"D9AE1600000031C7",
"D9AE1600000031E6",
"D9AE1600000031F4",
"D9AE1600000031F6",
"D9AE1600000031F8",
"D9AE1600000031FD",
"D9AE160000003203",
"D9AE160000003208",
"D9AE160000003209",
"D9AE16000000320F",
"D9AE160000003215",
"D9AE160000003217",
"D9AE160000003242",
"D9AE160000003247",
"D9AE160000003249",
"D9AE16000000324B",
"D9AE16000000324C",
"D9AE16000000324D",
"D9AE16000000324E",
"D9AE16000000324F",
"D9AE16000000325C",
"D9AE160000003260",
"D9AE160000003268",
"D9AE16000000326A",
"D9AE160000003272",
"D9AE16000000327F",
"D9AE160000003280",
"D9AE160000003281",
"D9AE160000003284",
"D9AE160000003286",
"D9AE160000003287",
"D9AE160000003288",
"D9AE160000003289",
"D9AE16000000328A",
"D9AE16000000328E",
"D9AE160000003295",
"D9AE1600000032A5",
"D9AE1600000032AB",
"D9AE1600000032AE",
"D9AE1600000032B0",
"D9AE1600000032B7",
"D9AE1600000032BB",
"D9AE1600000032D7",
"D9AE1600000032DC",
"D9AE1600000032E6",
"D9AE160000003302",
"D9AE160000003303",
"D9AE160000003312",
"D9AE16000000331C",
"D9AE16000000331D",
"D9AE16000000332B",
"D9AE16000000332F",
"D9AE160000003331",
"D9AE160000003344",
"D9AE160000003354",
"D9AE160000003356"
]

class TagUID():
    hwdb = {
        # 'C9BE1540100015B7': {'fwver': '01010D04', 'hwver': 0x53},
        # 'D9AE15000000096A': {'fwver': '01010D04', 'hwver': 0x53},
        # 'D9AE15000000148A': {'fwver': '01010D04', 'hwver': 0x53},
        # 'D9AE150000001664': {'fwver': '01010D04', 'hwver': 0x53},
        # 'D9AE1500000017AB': {'fwver': '01010D04', 'hwver': 0x53},
        # 'D9AE1500000026B3': {'fwver': '01010D04', 'hwver': 0x53},
        # 'D9AE150000002C06': {'fwver': '01010D04', 'hwver': 0x53},
        # 'D9AE150000002E1B': {'fwver': '01010D04', 'hwver': 0x53},
        # 'D9AE15000003666C': {'fwver': '01010D04', 'hwver': 0x53},
        # 'D9AE150006D07893': {'fwver': '01010D04', 'hwver': 0x53},
        # 'D9AE15010000965F': {'fwver': '01010D04', 'hwver': 0x53},
        # 'D9AE1600000027C2': {'fwver': '01010D04', 'hwver': 0x53},
        # 'D9AE160000003297': {'fwver': '01010D04', 'hwver': 0x53},
        # 'D9AE16000001226C': {'fwver': '01010D04', 'hwver': 0x53},
        # 'D9AE2303809A3092': {'fwver': '01010D04', 'hwver': 0x53},
        # 'D9EA1D4000001E1E': {'fwver': '01010D04', 'hwver': 0x53},
        # 'D98C112000002C4B': {'fwver': '01010D04', 'hwver': 0x53},
        # 'D9AA1A0000800228': {'fwver': '01010D04', 'hwver': 0x53},
        # 'D9AE14010004087C': {'fwver': '01010D04', 'hwver': 0x53},
        # 'D9AE1500000014B2': {'fwver': '01010D04', 'hwver': 0x53},

        'D9AE160000000192': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE16000000019A': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE16000000015D': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE160000000147': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE160000000196': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE1600000001A3': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE1600000001FD': {'fwver': '1050302', 'hwver': 0x33},
        'D9AE160000000272': {'fwver': '1050302', 'hwver': 0x33},
        'D9AE160000000268': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE1600000001E8': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE160000000263': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE1600000001B2': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE160000000163': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE1600000001AA': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE160000000211': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE160000000251': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE160000000148': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE16000000018F': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE160000000241': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE160000000242': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE160000000199': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE160000000142': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE1600000001DD': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE160000000146': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE16000000019D': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE160000000231': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE160000000195': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE16000000019C': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE1600000001AC': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE160000000220': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE16000000027E': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE160000000184': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE16000000021D': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE1600000001F0': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE16000000025F': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE160000000262': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE160000000252': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE160000000232': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE160000000214': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE16000000026C': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE160000000190': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE1600000001C0': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE1600000001FA': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE16000000026A': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE1600000001D8': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE16000000020F': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE1600000001EB': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE16000000018E': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE160000000253': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE1600000001CE': {'fwver': 'None', 'hwver': None},
        'D9AE16000000016C': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE160000000255': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE1600000001B0': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE1600000001AE': {'fwver': 'None', 'hwver': None},
        'D9AE16000000020E': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE16000000027C': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE1600000001E0': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE1600000001CD': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE16000000025B': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE160000000193': {'fwver': '1050302', 'hwver': 0x33},
        'D9AE1600000001C3': {'fwver': '1050302', 'hwver': 0x33},
        'D9AE1600000001B4': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE16000000024A': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE1600000001D4': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE16000000027A': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE16000000021A': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE16000000014F': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE160000000233': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE160000000201': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE160000000215': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE1600000001ED': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE1600000001A4': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE1600000001BB': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE160000000141': {'fwver': 'FC050600', 'hwver': 0x33},
        'D9AE160000000206': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE1600000001EA': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE160000000213': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE160000000207': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE160000000237': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE1600000001EF': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE16000000022F': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE1600000001D1': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE1600000001B9': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE16000000023F': {'fwver': 'None', 'hwver': None},
        'D9AE16000000016D': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE160000000170': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE16000000016A': {'fwver': 'None', 'hwver': None},
        'D9AE16000000020D': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE1600000001EC': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE160000000224': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE16000000022A': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE160000000256': {'fwver': '1050302', 'hwver': 0x33},
        'D9AE160000000227': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE160000000225': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE16000000015E': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE160000000203': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE1600000001A7': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE1600000001D2': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE1600000001C4': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE1600000001B7': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE16000000014B': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE16000000016F': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE1600000001DF': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE16000000022C': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE1600000001F1': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE160000000202': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE160000000174': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE160000000156': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE16000000022D': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE160000000162': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE1600000001D5': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE1600000001B8': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE160000000219': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE16000000024C': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE160000000277': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE16000000023D': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE160000000144': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE16000000020B': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE160000000239': {'fwver': '1050302', 'hwver': 0x33},
        'D9AE160000000185': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE160000000177': {'fwver': 'None', 'hwver': None},
        'D9AE1600000001C2': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE160000000236': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE1600000001A8': {'fwver': '1050302', 'hwver': 0x33},
        'D9AE16000000025E': {'fwver': 'None', 'hwver': None},
        'D9AE160000000209': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE160000000238': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE1600000001F5': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE16000000019E': {'fwver': 'None', 'hwver': None},
        'D9AE1600000001A1': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE1600000001E1': {'fwver': '1050302', 'hwver': 0x33},
        'D9AE1600000001A0': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE160000000205': {'fwver': 'None', 'hwver': None},
        'D9AE1600000001C6': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE1600000001F7': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE16000000014D': {'fwver': 'None', 'hwver': None},
        'D9AE1600000001A2': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE16000000025A': {'fwver': 'FC050600', 'hwver': 0x33},
        'D9AE1600000001CC': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE160000000210': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE16000000014C': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE160000000183': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE1600000001FB': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE16000000022B': {'fwver': 'None', 'hwver': None},
        'D9AE16000000027D': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE1A0019A4804B': {'fwver': 'None', 'hwver': None},
        'D9AE1600000001C9': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE160000000267': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE1600000001B1': {'fwver': '1050302', 'hwver': 0x33},
        'D9AE16000000024F': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE1600000001C5': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE160000000164': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE160000000250': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE160000000171': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE160000000266': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE1600000001E3': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE160000000243': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE160000000198': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE160000000258': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE160000000260': {'fwver': '1050302', 'hwver': 0x33},
        'D9AE16000000026D': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE160000000248': {'fwver': '1050302', 'hwver': 0x33},
        'D9AE160000000175': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE16000000016E': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE16000000026B': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE16000000019B': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE16000000014E': {'fwver': '1050302', 'hwver': 0x33},
        'D9AE160000000249': {'fwver': '1050302', 'hwver': 0x33},
        'D9AE16000000015C': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE16000000016B': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE1600000001DE': {'fwver': '1050302', 'hwver': 0x33},
        'D9AE1600000001E4': {'fwver': '1050302', 'hwver': 0x33},
        'D9AE16000000018D': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE160000000151': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE160000000264': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE160000000191': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE1600000001BA': {'fwver': '1050302', 'hwver': 0x33},
        'D9AE1600000001BF': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE160000000194': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE160000000254': {'fwver': 'None', 'hwver': None},
        'D9AE16000000022E': {'fwver': '1050302', 'hwver': 0x33},
        'D9AE160000000275': {'fwver': '1050302', 'hwver': 0x33},
        'D9AE1600000001C7': {'fwver': 'None', 'hwver': None},
        'D9AE1600000001F4': {'fwver': 'None', 'hwver': None},
        'D9AE160000000176': {'fwver': 'None', 'hwver': None},
        'D9AE160000000172': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE16000000020A': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE160000000153': {'fwver': '1050302', 'hwver': 0x33},
        'D9AE1600000001CB': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE160000000217': {'fwver': 'None', 'hwver': None},
        'D9AE16000000020C': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE16000000021F': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE16000000024E': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE1600000001E5': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE1600000001D3': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE16000000019F': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE16000000025D': {'fwver': '1050302', 'hwver': 0x33},
        'D9AE1600000001B5': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE1600000001BE': {'fwver': '1050302', 'hwver': 0x33},
        'D9AE16000000017C': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE16000000021C': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE16000000018A': {'fwver': '1050302', 'hwver': 0x33},
        'D9AE1600000001CF': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE16000000017E': {'fwver': 'FC050600', 'hwver': 0x33},
        'D9AE1600000001E6': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE16000000023E': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE1600000001BC': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE16000000023C': {'fwver': '1050302', 'hwver': 0x33},
        'D9AE16000000017D': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE16000000018C': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE160000000274': {'fwver': '1050302', 'hwver': 0x33},
        'D9AE1600000001F2': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE16000000023B': {'fwver': '1050302', 'hwver': 0x33},
        'D9AE160000000189': {'fwver': '1050302', 'hwver': 0x33},
        'D9AE160000000270': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE1600000001B6': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE160000000168': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE1A0019A47FF2': {'fwver': 'None', 'hwver': None},
        'D9AE1A0019A48036': {'fwver': 'None', 'hwver': None},
        'D9AE1600000001FF': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE16000000027F': {'fwver': 'None', 'hwver': None},
        'D9AE150000000495': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE1500000004F0': {'fwver': 'None', 'hwver': None},
        'D9AE15000000045C': {'fwver': 'None', 'hwver': None},
        'D9AE1500000004D4': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE15000000045E': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE150000000450': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE1500000004F3': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE1500000004F8': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE150000000510': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE15000000049A': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE1500000004E6': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE15000000044E': {'fwver': '1050302', 'hwver': 0x23},
        'D9AE1500000004AE': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE1500000004F9': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE1500000004F6': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE1500000004BC': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE15000000044D': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE1500000004C9': {'fwver': 'FC050600', 'hwver': 0x23},
        'D9AE15000000052C': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE1500000004D1': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE150000000529': {'fwver': 'None', 'hwver': None},
        'D9AE15000000045A': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE150000000454': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE1500000004A4': {'fwver': 'FC050600', 'hwver': 0x23},
        'D9AE150000000501': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE1500000004DA': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE150000000517': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE150000000463': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE1500000004F5': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE150000000459': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE1500000004CD': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE1500000004E1': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE15000000051D': {'fwver': 'None', 'hwver': None},
        'D9AE15000000051B': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE150000000506': {'fwver': 'None', 'hwver': None},
        'D9AE150000000520': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE1500000004B1': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE1500000003FE': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE15000000051E': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE150000000518': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE150000000516': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE1500000004C1': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE150000000491': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE15000000051F': {'fwver': 'FC050600', 'hwver': 0x23},
        'D9AE1500000004E8': {'fwver': 'FC050600', 'hwver': 0x23},
        'D9AE1500000004E7': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE150000000417': {'fwver': 'FC050600', 'hwver': 0x23},
        'D9AE150000000515': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE150000000504': {'fwver': 'FC050600', 'hwver': 0x23},
        'D9AE1500000004F2': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE150000000513': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE1500000004B0': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE150000000499': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE15000000043D': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE1500000004F1': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE1500000004F4': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE150000000508': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE15000000052B': {'fwver': 'None', 'hwver': None},
        'D9AE150000000521': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE150000000522': {'fwver': 'None', 'hwver': None},
        'D9AE1500000004E2': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE1500000004FC': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE150000000423': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE150000000527': {'fwver': 'None', 'hwver': None},
        'D9AE1500000004B2': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE150000000505': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE1500000004B7': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE1500000004BF': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE1500000004E5': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE1500000004CF': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE15000000052A': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE1500000004E3': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE1500000004DC': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE1500000004FF': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE1600000001F8': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE16000000017A': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE1600000001E7': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE160000000230': {'fwver': '1050302', 'hwver': 0x33},
        'D9AE16000000023A': {'fwver': '1050302', 'hwver': 0x33},
        'D9AE160000000154': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE1A0019A47FD3': {'fwver': 'None', 'hwver': None},
        'D9AE1A0019A47FD5': {'fwver': 'None', 'hwver': None},
        'D9AE1A0019A48028': {'fwver': 'None', 'hwver': None},
        'D9AE1A0019A48053': {'fwver': 'None', 'hwver': None},
        'D9AE1A0019A4806C': {'fwver': 'None', 'hwver': None},
        'D9AE1500000004BB': {'fwver': '1050302', 'hwver': 0x23},
        'D9AE140000000294': {'fwver': 'None', 'hwver': None},
        'D9AE16000000021E': {'fwver': '1050302', 'hwver': 0x33},
        'D9AE160000000149': {'fwver': '1050302', 'hwver': 0x33},
        'D9AE1600000001FC': {'fwver': 'None', 'hwver': None},
        'D9AE1600000001FE': {'fwver': '1050302', 'hwver': 0x33},
        'D9AE16000000024D': {'fwver': '1050302', 'hwver': 0x33},
        'D9AE1600000001F6': {'fwver': '1050302', 'hwver': 0x33},
        'D9AE160000000269': {'fwver': '1050302', 'hwver': 0x33},
        'D9AE160000000261': {'fwver': '1050302', 'hwver': 0x33},
        'D9AE160000000235': {'fwver': 'None', 'hwver': None},
        'D9AE16000000025C': {'fwver': '1050302', 'hwver': 0x33},
        'D9AE160000000245': {'fwver': '1050302', 'hwver': 0x33},
        'D9AE160000000155': {'fwver': 'None', 'hwver': None},
        'D9AE160000000247': {'fwver': '1050302', 'hwver': 0x33},
        'D9AE160000000178': {'fwver': '1050302', 'hwver': 0x33},
        'D9AE160000000200': {'fwver': '1050302', 'hwver': 0x33},
        'D9AE160000000246': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE160000000257': {'fwver': 'None', 'hwver': None},
        'D9AE160000000271': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE16000000017B': {'fwver': 'None', 'hwver': None},
        'D9AE1A0019A4805A': {'fwver': 'None', 'hwver': None},
        'D9AE1B0055550003': {'fwver': 'None', 'hwver': None},
        'D9AE1A0019A4802F': {'fwver': 'None', 'hwver': None},
        'D9AE1A0019A47FFD': {'fwver': 'None', 'hwver': None},
        'D9AE160000000280': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE1600000001C1': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE1400000007C4': {'fwver': 'None', 'hwver': None},
        'D9AE160000000265': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE160000000173': {'fwver': 'FC050600', 'hwver': 0x33},
        'D9AE160000000180': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE1A0019A47FEC': {'fwver': 'None', 'hwver': None},
        'D9AE1A0019A47FEB': {'fwver': 'None', 'hwver': None},
        'D9AE140000000800': {'fwver': '1050303', 'hwver': 0x31},
        '3D6E19EFC3BA95E0': {'fwver': 'None', 'hwver': None},
        '0AFC1905925F100F': {'fwver': 'None', 'hwver': None},
        '76CC19642C61F999': {'fwver': 'None', 'hwver': None},
        '0AFD192E7A6C2E0E': {'fwver': 'None', 'hwver': None},
        '1672193F79337376': {'fwver': 'None', 'hwver': None},
        '313119A176A7928E': {'fwver': 'None', 'hwver': None},
        '5C5C19E430E5D676': {'fwver': 'None', 'hwver': None},
        '76651993C8C7667A': {'fwver': 'None', 'hwver': None},
        '90F519D7AD789A5B': {'fwver': 'None', 'hwver': None},
        '8A2019EB43788CD8': {'fwver': 'None', 'hwver': None},
        '8AC419F1AD1CC599': {'fwver': 'None', 'hwver': None},
        '358119966A568AF0': {'fwver': 'None', 'hwver': None},
        'D9AE1500000004F7': {'fwver': 'FC050600', 'hwver': 0x23},
        'D9AE150000000526': {'fwver': '1050303', 'hwver': 0x23},
        'ACB7197F5F0D5D3C': {'fwver': 'None', 'hwver': None},
        'D9AE1500000004EE': {'fwver': '1050303', 'hwver': 0x23},
        '4D9819EAA174D855': {'fwver': 'None', 'hwver': None},
        'D9AE1500000004ED': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE150000000523': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE1500000004EF': {'fwver': '1050303', 'hwver': 0x23},
        'F2AC199ADC46EEE3': {'fwver': 'None', 'hwver': None},
        '29B019F6D27FADC5': {'fwver': 'None', 'hwver': None},
        'A5171911AE1110FD': {'fwver': 'None', 'hwver': None},
        'D9AE1600000001A6': {'fwver': '1050302', 'hwver': 0x33},
        'D9AE160000000160': {'fwver': 'None', 'hwver': None},
        'D9AE16000000015F': {'fwver': '1050302', 'hwver': 0x33},
        'D9AE16000000015B': {'fwver': 'None', 'hwver': None},
        'D9AE1600000001AB': {'fwver': '1050302', 'hwver': 0x33},
        'D9AE1600000001AD': {'fwver': '1050302', 'hwver': 0x33},
        '7C02197710529E15': {'fwver': 'None', 'hwver': None},
        'D9AE1600000001A9': {'fwver': '1050303', 'hwver': 0x33},
        'E04E19FE93264220': {'fwver': 'None', 'hwver': None},
        'D9AE1600000001A5': {'fwver': 'FC050600', 'hwver': 0x33},
        'D9AE160000000221': {'fwver': 'None', 'hwver': None},
        'D9AE160000000229': {'fwver': 'None', 'hwver': None},
        'D9AE160000000228': {'fwver': '1050302', 'hwver': 0x33},
        'D9AE1600000001E2': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE160000000188': {'fwver': 'None', 'hwver': None},
        'D9AE1600000001CA': {'fwver': '1050302', 'hwver': 0x33},
        'D9AE16000000018B': {'fwver': 'None', 'hwver': None},
        'D9AE160000000218': {'fwver': '1050302', 'hwver': 0x33},
        'D9AE1600000005AA': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE16000000056E': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE16000000063E': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE160000000503': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE1600000005A7': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE160000000587': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE1600000004FF': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE16000000054A': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE160000000608': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE160000000542': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE16000000052D': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE160000000524': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE160000000589': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE160000000522': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE16000000065A': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE1600000005B3': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE1600000005E9': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE1600000004A2': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE160000000546': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE1600000004DA': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE1600000004E5': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE160000000593': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE160000000627': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE16000000064A': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE16000000049E': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE1600000005A6': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE1600000004AD': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE1600000004ED': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE1600000004B7': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE1600000004EE': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE160000000616': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE1600000005E0': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE16000000065D': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE16000000055C': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE160000000598': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE160000000642': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE16000000049D': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE16000000065C': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE160000000492': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE160000000639': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE160000000599': {'fwver': '1050302', 'hwver': 0x33},
        'D9AE160000000635': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE1600000004FE': {'fwver': 'None', 'hwver': None},
        'D9AE16000000061B': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE16000000059E': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE160000000611': {'fwver': '1050303', 'hwver': 0x33},
        '6A6419A60699DEE4': {'fwver': 'None', 'hwver': None},
        'DC63194E0808B9BD': {'fwver': 'None', 'hwver': None},
        '8C4D198A955F7EE0': {'fwver': 'None', 'hwver': None},
        'F03019C0889CC663': {'fwver': 'None', 'hwver': None},
        'D9AE16000000041B': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE160000000456': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE1600000003D1': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE16000000045F': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE160000000417': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE1600000003E7': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE16000000045C': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE160000000179': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE160000000443': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE16000000043A': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE160000000431': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE160000000459': {'fwver': 'None', 'hwver': None},
        'D9AE160000000204': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE160000000226': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE160000000425': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE160000000438': {'fwver': 'None', 'hwver': None},
        'D9AE160000000440': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE1600000003E3': {'fwver': 'None', 'hwver': None},
        'D9AE160000000446': {'fwver': 'None', 'hwver': None},
        'D9AE160000000442': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE160000000441': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE1600000001F3': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE1600000003FE': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE1600000003DA': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE1600000005A8': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE16000000021B': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE1600000001EE': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE16000000058E': {'fwver': '1050302', 'hwver': 0x33},
        'D9AE150000000C44': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE1600000003F1': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE1500000007B4': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE1500000008D0': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE150000000C28': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE150000000C2B': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE150000000EA0': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE150000000747': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE15000000081D': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE150000000514': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE1500000006DD': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE150000000798': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE15000000073A': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE1500000006E5': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE150000000C2C': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE1500000006C7': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE150000000745': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE15000000088B': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE150000000C2D': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE150000000C34': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE1500000006DE': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE150000000C35': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE150000000C3B': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE150000000C3A': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE150000000E9B': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE150000000725': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE150000000C56': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE150000000EA2': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE150000000BC0': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE1500000004E9': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE150000000C0E': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE150000000BC8': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE150000000BC3': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE1500000004EA': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE150000000BC1': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE150000000C33': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE150000000C6C': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE1500000006E8': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE1500000004D8': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE1500000004EB': {'fwver': 'FC050600', 'hwver': 0x23},
        'D9AE1500000003A5': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE160000000534': {'fwver': '1050302', 'hwver': 0x33},
        'D9AE160000000549': {'fwver': 'None', 'hwver': None},
        'D9AE160000000649': {'fwver': '1050302', 'hwver': 0x33},
        'D9AE1600000005AD': {'fwver': '1050302', 'hwver': 0x33},
        'D9AE1600000005E8': {'fwver': '1050302', 'hwver': 0x33},
        'D9AE16000000049F': {'fwver': 'FC050600', 'hwver': 0x33},
        'D9AE16000000057E': {'fwver': 'FC050600', 'hwver': 0x33},
        'D9AE160000000536': {'fwver': 'FC050600', 'hwver': 0x33},
        'D9AE1600000005F0': {'fwver': '1050302', 'hwver': 0x33},
        'D9AE1600000004FA': {'fwver': 'FC050600', 'hwver': 0x33},
        'D9AE160000000561': {'fwver': 'FC050600', 'hwver': 0x33},
        'D9AE160000000525': {'fwver': '1050302', 'hwver': 0x33},
        'D9AE160000000659': {'fwver': '1050302', 'hwver': 0x33},
        'D9AE160000000538': {'fwver': '1050302', 'hwver': 0x33},
        'D9AE160000000643': {'fwver': '1050302', 'hwver': 0x33},
        'D9AE1600000005FC': {'fwver': 'FC050600', 'hwver': 0x33},
        'D9AE160000000597': {'fwver': '1050302', 'hwver': 0x33},
        'D9AE150000000E9C': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE16000000059D': {'fwver': '1050302', 'hwver': 0x33},
        'D9AE1600000005D3': {'fwver': '1050302', 'hwver': 0x33},
        'D9AE160000000529': {'fwver': '1050302', 'hwver': 0x33},
        'D9AE1600000005D7': {'fwver': '1050302', 'hwver': 0x33},
        'D9AE16000000059B': {'fwver': '1050302', 'hwver': 0x33},
        'D9AE160000000590': {'fwver': '1050302', 'hwver': 0x33},
        'D9AE15000000072A': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE150000000644': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE150000000EC4': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE1500000007B0': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE1600000004C6': {'fwver': '1050302', 'hwver': 0x33},
        'D9AE1500000007A4': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE1500000007B9': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE1500000006D6': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE15000000081C': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE150000000AFA': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE150000000890': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE150000000895': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE15000000088D': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE15000000089A': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE150000000EC0': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE1500000006BD': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE150000000EC5': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE15000000060F': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE15000000070D': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE1500000006E1': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE150000000882': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE150000000EAA': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE150000000C6A': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE1500000006C0': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE15000000088F': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE15000000088C': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE150000000EAB': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE15000000067C': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE150000000B17': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE150000000E79': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE150000000EA9': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE15000000069C': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE15000000073F': {'fwver': 'FC050600', 'hwver': 0x23},
        'D9AE150000000691': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE150000000B48': {'fwver': 'FC050600', 'hwver': 0x23},
        'D9AE150000000748': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE150000000894': {'fwver': 'FC050600', 'hwver': 0x23},
        'D9AE150000000892': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE150000000651': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE150000000EC6': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE150000000EBD': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE150000000881': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE150000000732': {'fwver': 'FC050600', 'hwver': 0x23},
        'D9AE150000000EB9': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE150000000C45': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE150000000EC2': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE1500000008D9': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE150000000C2A': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE150000000780': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE150000000C25': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE150000000EA1': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE150000000713': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE150000000622': {'fwver': 'FC050600', 'hwver': 0x23},
        'D9AE150000000C2F': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE150000000C19': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE160000000515': {'fwver': '1050302', 'hwver': 0x33},
        'D9AE160000000631': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE1600000004B4': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE16000000048B': {'fwver': 'FC050600', 'hwver': 0x33},
        'D9AE16000000050F': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE160000000554': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE1600000005C8': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE160000000491': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE1600000004F4': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE1600000004CA': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE1600000004EF': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE1600000005D5': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE1600000005BD': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE1600000004A7': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE160000000600': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE1600000004E8': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE1600000004A1': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE150000000711': {'fwver': '1050303', 'hwver': 0x23},
        'D9AE16000000060F': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE160000000511': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE160000000497': {'fwver': 'FC050600', 'hwver': 0x33},
        'D9AE160000000640': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE150000001325': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE15000000179E': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001560': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000013E4': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000013FF': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001555': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001852': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000015CA': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000013C5': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE15000000184E': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE15000000179F': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001329': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000013FE': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000014B8': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000014AE': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001403': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE150000001404': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000014AB': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE150000001778': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001400': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE15000000177C': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001940': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001521': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001786': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000015F1': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE15000000132D': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001568': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000014B7': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001395': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001845': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001851': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000014F0': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001618': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000016D9': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000017AE': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000016C1': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001737': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000016D0': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000016BC': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000001455': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001623': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000015F5': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000017DD': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000015F8': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001617': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE15000000160E': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001488': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001793': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000014E3': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001979': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE15000000133A': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000012D2': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000015B7': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000013AA': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE15000000125E': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001267': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001578': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001659': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000015F0': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000017A9': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000013C1': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001409': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001337': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001721': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000012C7': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001887': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE15000000143B': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001938': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000014E4': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE15000000174C': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001310': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE15000000174E': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE15000000142D': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE15000000175D': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE15000000143C': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001751': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001780': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001566': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000014FC': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE15000000155E': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000014F7': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001935': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE15000000156C': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001564': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001571': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000013C9': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001449': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001427': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000013C7': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001452': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE15000000156E': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001444': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001328': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001323': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001755': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE15000000167A': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000017F1': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000017EC': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001963': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000017DC': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000017E5': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000017E7': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000017E4': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000017DF': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000014BA': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000014B9': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE15000000171C': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE15000000171A': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000017AA': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000001422': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE15000000179A': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001606': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000017A1': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001607': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000001657': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001796': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000018AF': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000018B5': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000018A4': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000018A5': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE15000000142F': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000014B6': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000018A6': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE15000000141B': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000001990': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE15000000144B': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000017F5': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000001715': {'fwver': 'None', 'hwver': None},
        'D9AE1500000017F8': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000017F3': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE15000000199A': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000001785': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE150000001994': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000001735': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001563': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001605': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001992': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE15000000189D': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE15000000133F': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000018A7': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000018AD': {'fwver': 'None', 'hwver': None},
        'D9AE1500000015F2': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000012C9': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000019DA': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE15000000132A': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000017A7': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001358': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000019CE': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE15000000170B': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000001993': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000001773': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001711': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000012DF': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000001801': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE15000000195E': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE160000000655': {'fwver': '1050302', 'hwver': 0x33},
        'D9AE150000001332': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE15000000130B': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000001908': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000001393': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000017B2': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000016A5': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE15000000172E': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000001632': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE15000000184D': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001675': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000016CC': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE15000000130D': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001921': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE15000000159A': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000016EA': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000016DF': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001F6E': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000000ADA': {'fwver': 'FC050600', 'hwver': 0x23},
        'D9AE1500000018C2': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001F77': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000016BD': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE15000000190A': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000001441': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000001F58': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001110': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001265': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE15000000170D': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001F98': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000015D7': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000000EFF': {'fwver': '1060001', 'hwver': 0x23},
        'D9AE150000001E90': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000001D90': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001F70': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001DF6': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000018DD': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001E38': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000001543': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000018AE': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000015B3': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000012D7': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000013EE': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000001D98': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000016E7': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001F8E': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE15000000139D': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000015B5': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001DFD': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000001612': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000015D6': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001F75': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000012F7': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE15000000170A': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000015C1': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001669': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001E1E': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001674': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001F6B': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001F71': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000001326': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000001E09': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000012D3': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001EC6': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001E84': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE15000000186F': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000001842': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001394': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001E02': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001319': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000019E1': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000001E86': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001F6A': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000016BA': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000002077': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000002079': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001EAD': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001E1B': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001F42': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001D13': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE15000000131A': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001760': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000001F82': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001E41': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000001D86': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001945': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000016E8': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001482': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000016AE': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE15000000126D': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000001350': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE15000000168F': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000001388': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000015AC': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000016E2': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000016B7': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000016BF': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000001E2E': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000001E4E': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001E0B': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002084': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001E0A': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000001DFE': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000001F95': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000015B9': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000013B5': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE15000000130C': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001732': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000015C0': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE15000000139F': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000013A5': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE15000000166C': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000001E07': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000001865': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000001485': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000013F4': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000015B0': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE15000000173B': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001263': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE15000000187B': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000018B9': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001892': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000014FF': {'fwver': 'None', 'hwver': None},
        'D9AE1500000014BB': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000015DE': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001710': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000018C4': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000000778': {'fwver': '1060001', 'hwver': 0x23},
        'D9AE15000000131E': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE15000000205C': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE15000000166E': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE15000000172D': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000012DC': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001672': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000012DB': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000018FD': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000000C37': {'fwver': '1060001', 'hwver': 0x23},
        'D9AE150000001D50': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000000994': {'fwver': '1060001', 'hwver': 0x23},
        'D9AE150000000C49': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000000FBD': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000000FF3': {'fwver': '1060001', 'hwver': 0x23},
        'D9AE150000001577': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000013DC': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000000BEA': {'fwver': '1060001', 'hwver': 0x23},
        'D9AE15000000171F': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001DED': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001D4F': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001D41': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001DF8': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000000FE3': {'fwver': '1060001', 'hwver': 0x23},
        'D9AE1500000019DB': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000000BAC': {'fwver': '1060001', 'hwver': 0x23},
        'D9AE150000000F5B': {'fwver': '1060001', 'hwver': 0x23},
        'D9AE150000001EAE': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000000C04': {'fwver': '1060001', 'hwver': 0x23},
        'D9AE150000000EB2': {'fwver': '1060001', 'hwver': 0x23},
        'D9AE150000000E67': {'fwver': '1060001', 'hwver': 0x23},
        'D9AE150000000B5A': {'fwver': '1060001', 'hwver': 0x23},
        'D9AE150000000BFF': {'fwver': '1060001', 'hwver': 0x23},
        'D9AE15000000202F': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000000E77': {'fwver': 'FC050600', 'hwver': 0x23},
        'D9AE150000000F30': {'fwver': '1060001', 'hwver': 0x23},
        'D9AE150000000C0D': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000000B02': {'fwver': '1060001', 'hwver': 0x23},
        'D9AE15000000174B': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001472': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000008C6': {'fwver': 'FC050600', 'hwver': 0x23},
        'D9AE150000001FEE': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000000BB4': {'fwver': '1060001', 'hwver': 0x23},
        'D9AE15000000167C': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000000F56': {'fwver': '1060001', 'hwver': 0x23},
        'D9AE150000001615': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000020A4': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000014BF': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000000B12': {'fwver': '1060001', 'hwver': 0x23},
        'D9AE15000000097E': {'fwver': '1060001', 'hwver': 0x23},
        'D9AE150000000715': {'fwver': '1060001', 'hwver': 0x23},
        'D9AE150000000B5D': {'fwver': '1060001', 'hwver': 0x23},
        'D9AE150000000C40': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000000F96': {'fwver': '1060001', 'hwver': 0x23},
        'D9AE1500000005FE': {'fwver': '1060001', 'hwver': 0x23},
        'D9AE150000001CF3': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000000EE8': {'fwver': '1060001', 'hwver': 0x23},
        'D9AE150000000C30': {'fwver': '1060001', 'hwver': 0x23},
        'D9AE150000001EB4': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000000F0E': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000000C09': {'fwver': '1060001', 'hwver': 0x23},
        'D9AE150000000F36': {'fwver': '1060001', 'hwver': 0x23},
        'D9AE150000001EB5': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001924': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000015A3': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000018BC': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001FFB': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001D53': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000020A3': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001D9A': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000018C0': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001690': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000000AFB': {'fwver': '1060001', 'hwver': 0x23},
        'D9AE150000000EE4': {'fwver': '1060001', 'hwver': 0x23},
        'D9AE150000000AFF': {'fwver': '1060001', 'hwver': 0x23},
        'D9AE150000000B83': {'fwver': '1060001', 'hwver': 0x23},
        'D9AE150000001774': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000000BFC': {'fwver': '1060001', 'hwver': 0x23},
        'D9AE150000001514': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE15000000202E': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000017BA': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000000B07': {'fwver': '1060001', 'hwver': 0x23},
        'D9AE150000001655': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000000995': {'fwver': '1060001', 'hwver': 0x23},
        'D9AE150000000A56': {'fwver': '1060001', 'hwver': 0x23},
        'D9AE150000001FF0': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000000B20': {'fwver': '1060001', 'hwver': 0x23},
        'D9AE150000000C64': {'fwver': '1060001', 'hwver': 0x23},
        'D9AE15000000191E': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE160000000567': {'fwver': '1050302', 'hwver': 0x33},
        'D9AE1600000005DA': {'fwver': '1050302', 'hwver': 0x33},
        'D9AE1600000001F9': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE150000001905': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000015BD': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE15000000162B': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000012C1': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE150000001661': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE150000001622': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000013FB': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000001303': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001456': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000002071': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001F35': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE15000000125D': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001F72': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001321': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001F5A': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000015B2': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000016D8': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000016DC': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001458': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001F80': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000018B8': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000012D5': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000019EA': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001E82': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001E8D': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001327': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001F81': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001805': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE15000000133B': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000002076': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001D14': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE15000000166F': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001F62': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE15000000186D': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001345': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001301': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE15000000144F': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001629': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000012F6': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000012F0': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001705': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE15000000126F': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001262': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001631': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000012FC': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001261': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE15000000155A': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000012E4': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001308': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000012E3': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001763': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000015C7': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001702': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000015CE': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001504': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001256': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001362': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE15000000130F': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE15000000135D': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001397': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001E89': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001302': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE15000000132B': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001904': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001E2B': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000018FE': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001355': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001476': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE15000000130E': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001901': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001F91': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001407': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001900': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000012D1': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001855': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001768': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000012D4': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE15000000130A': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001619': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE15000000186A': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000015B8': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001628': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE15000000133C': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000012C4': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE15000000126E': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001304': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE15000000140E': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001391': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001853': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001F5E': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001FD3': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000019E8': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000019C5': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000001479': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE15000000139C': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE15000000170E': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000008DC': {'fwver': 'FC050600', 'hwver': 0x23},
        'D9AE15000000151F': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000000A18': {'fwver': 'FC050600', 'hwver': 0x23},
        'D9AE15000000205F': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000001559': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000007F7': {'fwver': 'FC050600', 'hwver': 0x23},
        'D9AE1500000017FF': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE15000000135E': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000001315': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000001525': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE15000000170F': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000000893': {'fwver': 'FC050600', 'hwver': 0x23},
        'D9AE15000000137D': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE15000000146F': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000001754': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000001581': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000001484': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000013A6': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000016B5': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000016D7': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000001462': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000001221': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000012D6': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000007F0': {'fwver': 'FC050600', 'hwver': 0x23},
        'D9AE150000001E03': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000009F3': {'fwver': 'FC050600', 'hwver': 0x23},
        'D9AE1500000016CA': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000001376': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000000A10': {'fwver': 'FC050600', 'hwver': 0x23},
        'D9AE15000000097C': {'fwver': 'FC050600', 'hwver': 0x23},
        'D9AE1500000016C2': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000001486': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000013BF': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000015CB': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE15000000170C': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE15000000148D': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000001708': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000000827': {'fwver': 'FC050600', 'hwver': 0x23},
        'D9AE150000001729': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000001656': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000016AD': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000008C3': {'fwver': 'FC050600', 'hwver': 0x23},
        'D9AE1500000016A8': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000001366': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000013EC': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000000B7B': {'fwver': 'FC050600', 'hwver': 0x23},
        'D9AE150000001722': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000001353': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000001223': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000008A1': {'fwver': 'None', 'hwver': None},
        'D9AE1500000013B8': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE15000000151A': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE15000000134E': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000001474': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000001389': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE15000000137F': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000012CC': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000001414': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000010CC': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000001429': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000001126': {'fwver': 'FC050600', 'hwver': 0x23},
        'D9AE150000001257': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000000F39': {'fwver': 'FC050600', 'hwver': 0x23},
        'D9AE150000001316': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE1600000004B2': {'fwver': 'FC050600', 'hwver': 0x33},
        'D9AE150000001DCA': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000012FF': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001351': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001307': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001291': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1600000005B2': {'fwver': 'FC050600', 'hwver': 0x33},
        'D9AE16000000041F': {'fwver': 'FC050600', 'hwver': 0x33},
        'D9AE150000001225': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000001365': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000016AC': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000016A4': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE150000001300': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE15000000138E': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000013A7': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000015C8': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000016A3': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000018A3': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000016AB': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001696': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE15000000175A': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001880': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001767': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000016C0': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000012E8': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000016DB': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000016B6': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE15000000168D': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE15000000176B': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001367': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001635': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE15000000142B': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000001428': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE15000000148E': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE15000000079B': {'fwver': '1060001', 'hwver': 0x23},
        'D9AE150000001324': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE15000000139E': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000000FAD': {'fwver': '1060001', 'hwver': 0x23},
        'D9AE15000000088E': {'fwver': '1060001', 'hwver': 0x23},
        'D9AE1500000013F6': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001416': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000016F5': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE15000000162A': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000012CF': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE15000000169A': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE15000000126A': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000018FA': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000016D3': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000016AF': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE15000000165C': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000013AE': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000000F61': {'fwver': '1060001', 'hwver': 0x23},
        'D9AE150000001916': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001483': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE15000000149A': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000013A9': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000013A8': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000000804': {'fwver': '1060001', 'hwver': 0x23},
        'D9AE1500000013B7': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE15000000197A': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000013FD': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001586': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE15000000196E': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE15000000147D': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000018E5': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000016B9': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000014DA': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001116': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000014F2': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001903': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001374': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000016D6': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE15000000132F': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000016C5': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001129': {'fwver': '1060001', 'hwver': 0x23},
        'D9AE150000001874': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000000E6A': {'fwver': '1060001', 'hwver': 0x23},
        'D9AE1500000019E7': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001224': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000000C11': {'fwver': '1060001', 'hwver': 0x23},
        'D9AE150000000897': {'fwver': '1060001', 'hwver': 0x23},
        'D9AE150000000A06': {'fwver': '1060001', 'hwver': 0x23},
        'D9AE1500000014AD': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001719': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001211': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001419': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001922': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000015BF': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000000B28': {'fwver': '1060001', 'hwver': 0x23},
        'D9AE1500000008CD': {'fwver': '1060001', 'hwver': 0x23},
        'D9AE150000000E87': {'fwver': '1060001', 'hwver': 0x23},
        'D9AE150000001227': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000012B4': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE15000000112B': {'fwver': '1060001', 'hwver': 0x23},
        'D9AE150000001716': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001553': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001492': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001128': {'fwver': 'FC050600', 'hwver': 0x23},
        'D9AE150000000752': {'fwver': 'FC050600', 'hwver': 0x23},
        'D9AE1500000004EC': {'fwver': 'FC050600', 'hwver': 0x23},
        'D9AE15000000190D': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000016C9': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000018B3': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000013B6': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000016BB': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE15000000186E': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001666': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001909': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001228': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000007FF': {'fwver': '1060001', 'hwver': 0x23},
        'D9AE150000001127': {'fwver': '1060001', 'hwver': 0x23},
        'D9AE150000000C2E': {'fwver': '1060001', 'hwver': 0x23},
        'D9AE1500000016CB': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001929': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE15000000138D': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE15000000186C': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000012C5': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000013AB': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000018D9': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001930': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE15000000193D': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000015D8': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000001714': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE15000000188D': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001910': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001955': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000016F0': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000000E6E': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001654': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001936': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001888': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE15000000159F': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001961': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001739': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001937': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001964': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001956': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE15000000195A': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000018EA': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000016F4': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000017D9': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001596': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000018A2': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000018F4': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE15000000184B': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE15000000080F': {'fwver': '1060001', 'hwver': 0x23},
        'D9AE150000001594': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000006A5': {'fwver': '1060001', 'hwver': 0x23},
        'D9AE150000001590': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE15000000081B': {'fwver': '1060001', 'hwver': 0x23},
        'D9AE150000002045': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE1600000003E5': {'fwver': '1050303', 'hwver': 0x33},
        'D9AE15000000176F': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000013AC': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000018E2': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000000EE7': {'fwver': 'FC050600', 'hwver': 0x23},
        'D9AE1500000006F4': {'fwver': 'FC050600', 'hwver': 0x23},
        'D9AE1500000019BC': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000001461': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000018E9': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000016DA': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000009E2': {'fwver': 'FC050600', 'hwver': 0x23},
        'D9AE150000000C5E': {'fwver': 'FC050600', 'hwver': 0x23},
        'D9AE150000001599': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002293': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000001ED5': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000022A1': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002031': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE15000000210D': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000001E22': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000000FF0': {'fwver': 'FC050600', 'hwver': 0x23},
        'D9AE150000000EEC': {'fwver': 'FC050600', 'hwver': 0x23},
        'D9AE1500000016B2': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002291': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000021A3': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000000A43': {'fwver': 'FC050600', 'hwver': 0x23},
        'D9AE15000000169B': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002177': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000001718': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000001F6F': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000020DF': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE15000000200A': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000021C4': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000000F29': {'fwver': 'FC050600', 'hwver': 0x23},
        'D9AE150000000FDB': {'fwver': 'FC050600', 'hwver': 0x23},
        'D9AE1500000020DB': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000001489': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000000E8F': {'fwver': 'FC050600', 'hwver': 0x23},
        'D9AE150000000FF5': {'fwver': 'FC050600', 'hwver': 0x23},
        'D9AE150000001DE2': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000001DD0': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000016CE': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE15000000204F': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000001FEC': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000012F4': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000010B1': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE15000000188A': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000018EB': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE15000000136F': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE15000000153A': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002157': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000000FE5': {'fwver': 'FC050600', 'hwver': 0x23},
        'D9AE1500000018C5': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000000C1D': {'fwver': 'FC050600', 'hwver': 0x23},
        'D9AE150000000B9B': {'fwver': 'FC050600', 'hwver': 0x23},
        'D9AE1500000020E5': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000001558': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000001FF3': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000001948': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000000C69': {'fwver': 'FC050600', 'hwver': 0x23},
        'D9AE150000001349': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000001F01': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000019A9': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000001DE1': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000001295': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000020FE': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE15000000069E': {'fwver': 'FC050600', 'hwver': 0x23},
        'D9AE1500000019AD': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000000793': {'fwver': 'FC050600', 'hwver': 0x23},
        'D9AE150000001F10': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000018CE': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000000FCB': {'fwver': 'FC050600', 'hwver': 0x23},
        'D9AE150000001782': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000018B4': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000001487': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000001665': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000019E3': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE15000000215B': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000022C8': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000021CC': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000001694': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE15000000216D': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000022D9': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000000FDD': {'fwver': 'FC050600', 'hwver': 0x23},
        'D9AE150000001982': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000020D7': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000012A2': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000015A5': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE15000000194A': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000001FB5': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000016EC': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000007FE': {'fwver': 'FC050600', 'hwver': 0x23},
        'D9AE1500000018F9': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000000C42': {'fwver': 'FC050600', 'hwver': 0x23},
        'D9AE150000001354': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE15000000204A': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000007BC': {'fwver': 'FC050600', 'hwver': 0x23},
        'D9AE150000000733': {'fwver': 'FC050600', 'hwver': 0x23},
        'D9AE1500000021B4': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE15000000200B': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000000C4C': {'fwver': 'FC050600', 'hwver': 0x23},
        'D9AE1500000020EB': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000018F5': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000001962': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000000776': {'fwver': 'FC050600', 'hwver': 0x23},
        'D9AE1500000018D7': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000000A41': {'fwver': 'FC050600', 'hwver': 0x23},
        'D9AE150000000E6D': {'fwver': 'FC050600', 'hwver': 0x23},
        'D9AE1500000021DC': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000016A9': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE15000000158D': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000019EE': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000019DC': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE15000000159E': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000015A8': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE15000000150D': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE15000000143F': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000018E4': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000001322': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE15000000225B': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000000C5F': {'fwver': 'FC050600', 'hwver': 0x23},
        'D9AE1500000015BA': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE15000000215F': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE15000000150A': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000001D5A': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE15000000196C': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000000E9D': {'fwver': 'FC050600', 'hwver': 0x23},
        'D9AE150000000EDB': {'fwver': 'FC050600', 'hwver': 0x23},
        'D9AE150000002159': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000000FFA': {'fwver': 'FC050600', 'hwver': 0x23},
        'D9AE150000001595': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000001DF7': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002187': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000020A5': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000018BD': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000000EDA': {'fwver': 'FC050600', 'hwver': 0x23},
        'D9AE1500000006A6': {'fwver': 'FC050600', 'hwver': 0x23},
        'D9AE1500000021BA': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002116': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE15000000219C': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000001D01': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000013DF': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000021E8': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000001934': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000000FB4': {'fwver': 'FC050600', 'hwver': 0x23},
        'D9AE15000000166A': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000001F0A': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000001EB7': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE15000000163E': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000016E5': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000001431': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000001772': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000006BC': {'fwver': 'FC050600', 'hwver': 0x23},
        'D9AE1500000014B5': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE15000000188B': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000015A0': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000006A8': {'fwver': 'FC050600', 'hwver': 0x23},
        'D9AE1500000018EC': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000001D7E': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002163': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000001F24': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE15000000011A': {'fwver': 'None', 'hwver': None},
        'D9AE1500000022A0': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000002232': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000020DC': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000021C2': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE15000000214D': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001EDC': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000013ED': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001958': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000016FF': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000021B7': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001907': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000000696': {'fwver': '1060001', 'hwver': 0x23},
        'D9AE150000000F62': {'fwver': '1060001', 'hwver': 0x23},
        'D9AE1500000022FB': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001709': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE15000000149C': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000021C3': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000000BB6': {'fwver': '1060001', 'hwver': 0x23},
        'D9AE150000001643': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001FEA': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000000C55': {'fwver': '1060001', 'hwver': 0x23},
        'D9AE1500000019D4': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000018AB': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE15000000131F': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001971': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000018DA': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001960': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000019AB': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000000F59': {'fwver': '1060001', 'hwver': 0x23},
        'D9AE15000000148C': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000000607': {'fwver': '1060001', 'hwver': 0x23},
        'D9AE1500000018F6': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000018DF': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001222': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE15000000248A': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001290': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000013FA': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000002493': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000019EB': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001717': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001330': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000019B1': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001597': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000002022': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000000ECC': {'fwver': '1060001', 'hwver': 0x23},
        'D9AE150000002046': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001F92': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001918': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000020F2': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000021C6': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000019E9': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000002308': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002491': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000002483': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000023B8': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000002034': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000023D7': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000021C5': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000018D8': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE160000001D6F': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE160000001D71': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE150000001996': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000000FFF': {'fwver': '1060001', 'hwver': 0x23},
        'D9AE15000000196B': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000000E65': {'fwver': '1060001', 'hwver': 0x23},
        'D9AE1500000019B2': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000015C9': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE15000000189E': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000002036': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000018ED': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000000FD1': {'fwver': '1060001', 'hwver': 0x23},
        'D9AE150000001968': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE15000000159D': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000015A1': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000007B7': {'fwver': '1060001', 'hwver': 0x23},
        'D9AE1500000018A9': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001977': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001459': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001939': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000002053': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000017A6': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001676': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001670': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000015C6': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE160000001DC0': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE150000001860': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000014E9': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001857': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE15000000185F': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE1500000014FD': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE1500000017BF': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000002154': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE150000002597': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE15000000125A': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE1500000017A2': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE15000000152B': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE150000001501': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE15000000193A': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE1500000012BE': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE1500000015CC': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE150000001797': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE15000000178D': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE150000001646': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE15000000171D': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE15000000217B': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE1500000017D3': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE150000001FDE': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE15000000163D': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE150000002560': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000017B7': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE150000001798': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE15000000125C': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE150000001440': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE1500000017B8': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE1500000017C6': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE1500000017B6': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE150000001343': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE150000001494': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE150000001781': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE1500000015A7': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE150000001727': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE15000000187A': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE15000000152E': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE150000001836': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE150000001EF0': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE15000000097B': {'fwver': 'FC050600', 'hwver': 0x23},
        'D9AE15000000187F': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE1500000015AF': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE1500000018E0': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE150000001457': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE150000001463': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE15000000134C': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE150000001451': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE150000001604': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE150000001794': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE1500000017DE': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE1500000017D8': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE1500000015EF': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE15000000168E': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE150000001747': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE150000001706': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE150000001435': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE150000001644': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE15000000215A': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE1500000015FB': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE15000000173C': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE1500000012B9': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE15000000172F': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE150000001530': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE15000000157B': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE1500000016A7': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE15000000181A': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE150000001658': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE15000000181C': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE1500000014FB': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE15000000183F': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE15000000160F': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE150000001764': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE1500000013D0': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE160000001D5A': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE160000001D3D': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE160000001D9E': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE160000001D9A': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE160000001D7D': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE160000001D4B': {'fwver': 'FC050600', 'hwver': 0x34},
        '330832B4D9AE1600': {'fwver': 'None', 'hwver': None},
        'D9AE160000001D9C': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE160000001DA0': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE160000001DA9': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE160000001D88': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE160000001D9B': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE160000001D8F': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE160000001D7C': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE160000001D84': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE160000001D72': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE160000001D73': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE160000001D7B': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE160000001DA1': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE160000001DA6': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE160000001D8D': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE160000001D8E': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE160000001D93': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE160000001DBE': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE160000001D3C': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE1500000024B4': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE15000000236E': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000024F5': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE15000000234E': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001357': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE15000000230C': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE1500000015EE': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE1500000016D5': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE150000001346': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE1500000014A1': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE1500000015D4': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE150000001591': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE15000000147F': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE150000001E26': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE1500000012C6': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE150000000EEB': {'fwver': 'FC050600', 'hwver': 0x23},
        'D9AE150000001753': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE150000002054': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE150000002182': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE15000000169D': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000016E9': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE1500000017E6': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE150000001776': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000001FEB': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE150000001752': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000017B9': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE15000000164A': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE150000001588': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE1500000022AE': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE150000001872': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE150000001572': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE150000001340': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE15000000069F': {'fwver': 'FC050600', 'hwver': 0x23},
        'D9AE15000000180B': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE1500000015B4': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE150000001697': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE1500000017A0': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE15000000168C': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE150000001790': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE15000000199E': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001593': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000024FA': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000024C4': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002463': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000023FA': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002541': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000023D9': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE15000000246C': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000023B5': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002488': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002572': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000025A9': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002588': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002598': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000024C7': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE15000000254A': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000024C8': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002585': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000025C5': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002591': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002563': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002556': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE15000000256C': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002579': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000025D5': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002548': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000024D1': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000024D0': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002514': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002512': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002509': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002428': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE15000000244D': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000024E4': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE15000000245A': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE15000000232A': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002426': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002460': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE15000000232B': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE15000000245B': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE15000000251D': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE15000000238C': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002425': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000023AF': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002345': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002587': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002599': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000023E4': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE15000000249D': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002528': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000024A2': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000025D8': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000024A3': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE15000000249A': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002529': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002589': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002449': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002544': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002522': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE15000000251F': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000024D3': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000024A4': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE15000000249B': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000025AA': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002380': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE15000000245C': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000025A4': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE15000000237F': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000023B2': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002481': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000023DC': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE15000000253E': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002495': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002596': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE15000000256D': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000024A9': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002486': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE15000000256A': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002574': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002489': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000024BB': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002570': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000024D8': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002584': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002577': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002592': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000025D6': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002581': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002533': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000024CB': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000024E8': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE15000000250E': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE15000000250D': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE15000000249E': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE15000000250B': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE15000000250C': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000024F7': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002475': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000024E1': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE15000000247B': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002427': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002446': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002378': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002326': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002335': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE15000000241B': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE15000000241C': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002473': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000024FC': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002500': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000024ED': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002550': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000025A5': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE15000000257B': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000025CA': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002583': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002586': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000024B5': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000024B7': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000024B2': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000025A7': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000024A5': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002524': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE15000000249F': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002374': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000024EF': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002363': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002381': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002370': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE15000000236F': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000023BE': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000023FC': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002545': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002328': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000023AB': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000025D4': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000023E2': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE15000000246F': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE15000000240D': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000023CD': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000023DB': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000024A1': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002547': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002358': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002356': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002424': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002376': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000023D4': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002366': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002355': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002430': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002372': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE15000000232D': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002340': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000024E5': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002568': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002566': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002431': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000023EC': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE15000000246E': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002352': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE15000000234B': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000017BC': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE15000000233D': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000023A1': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002382': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002377': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000017BE': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE150000001787': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE1500000024A7': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000024B1': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000017C0': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE150000001847': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE150000001480': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE15000000183D': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE1500000012DA': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE1500000015CD': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001689': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE150000002521': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000024DC': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE15000000257D': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000001699': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000001625': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE1500000017C1': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE1500000014F9': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE16000000237A': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE16000000235C': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE150000002DA6': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE1500000017AC': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE150000001396': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE15000000176A': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE1500000024DF': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE15000000167E': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE150000001359': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE15000000163A': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE1500000012E5': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE1500000017BB': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE1500000015D1': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE1500000012CB': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE150000002CA5': {'fwver': '1060001', 'hwver': 0x24},
        'D9AE150000002573': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000001688': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE1500000024FF': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000001633': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE1500000015E9': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE150000001724': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE1500000017A5': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE150000001445': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE15000000177B': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE1500000024DD': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE15000000252E': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000012EC': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE150000001771': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE1500000017ED': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE1500000015C5': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE150000002DA7': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002DD1': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002CC1': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1600000019ED': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE1600000023CE': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE160000001C73': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE160000001A42': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE1600000019DB': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE160000002363': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE160000001A07': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE160000001A70': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE160000002362': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE160000001A72': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE1600000019E9': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE160000001A54': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE150000002CBC': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE16000000237E': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE160000002373': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE16000000237C': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE150000001426': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE150000001712': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE150000001876': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE1600000023AD': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE15000000176E': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE1500000015CF': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE160000002374': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE16000000236E': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE15000000169C': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE150000001424': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE150000001765': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE15000000182B': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE150000002554': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000015BB': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE1500000014E7': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE160000002351': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE150000002DF5': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002DDE': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE160000002357': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE16000000234D': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE15000000071C': {'fwver': 'FC050600', 'hwver': 0x23},
        'D9AE150000002CBB': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002CBF': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000001602': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE150000001730': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE15000000254F': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000001726': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE15000000162E': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE150000002CB5': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002555': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1600000027D5': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE1600000027F1': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE160000002818': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE1600000027E8': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE1600000025D9': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE160000002634': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE1600000027DA': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE160000002804': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE160000002802': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE160000002595': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE160000002812': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE1600000027FA': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE1600000027E1': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE1600000027DF': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE150000002DD5': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1600000027E7': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE150000002CB3': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1600000027C4': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE150000002E17': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002CC2': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002E2B': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1600000027C0': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE1600000027CD': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE1600000027CA': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE1600000027C9': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE1600000027E9': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE1600000027BF': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE1600000027CB': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE150000002DFF': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1600000027E3': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE1600000027E6': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE1600000027E2': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE150000002D53': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002CE1': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002DC2': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002CCC': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002E2E': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002E33': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002CDF': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002E2D': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002E2A': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002E1D': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002DBD': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002E0D': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002CA6': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002E1E': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002E16': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002DB2': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002E34': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002E19': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002E06': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002E08': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002DC7': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002CC9': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002DB3': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002CCA': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002C14': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002CD5': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002C13': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002C4B': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002E31': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002CBE': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002CAE': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002DCF': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002CC3': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE160000002506': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE1600000026D2': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE1600000026E0': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE160000002559': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE160000002821': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE160000002510': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE1600000027C1': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE1600000024A2': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE1600000027D7': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE1600000027C5': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE1600000027EA': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE1600000027C8': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE1600000027C7': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE1600000027C6': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE1600000024D7': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE1600000026B6': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE1600000024CB': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE1600000024D9': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE1600000026A6': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE1600000024D6': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE160000002545': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE160000002730': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE1600000023FB': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE160000001C33': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE1600000025E1': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE16000000253C': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE150000002E0F': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002E23': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1600000026CB': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE160000001B48': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE16000000250D': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE160000001B8F': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE16000000249D': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE1600000024C7': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE160000001ABC': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE1600000023F6': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE1600000023FC': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE160000002512': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE160000002481': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE16000000251E': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE160000001B4E': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE150000002E2C': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002CC8': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002CC7': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002E24': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002DB0': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000028EB': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE160000001B82': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE16000000272B': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE1600000024C1': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE150000002E26': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002C50': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000003A67': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002E12': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE160000002511': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE1600000026D7': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE1600000024C3': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE1600000026B0': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE160000001C58': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE150000003A47': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1600000026CE': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE1600000025C8': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE160000001B89': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE150000003A66': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000003A42': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002DB9': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002E04': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000024C2': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE160000002520': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE1600000025E0': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE1600000025A5': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE1600000025FD': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE150000003A65': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000003A3F': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000003A52': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000003A3D': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000003A3E': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000003A49': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000003A38': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000003A44': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000003A40': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000003A48': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000003A4D': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000003A3A': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000003A68': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000003A5C': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000003A64': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000003A61': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000003A39': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000003A51': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002E0A': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002D0F': {'fwver': 'None', 'hwver': None},
        'D9AE150000003B5D': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002E35': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000003BF1': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000003BF8': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000003BBF': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1600000027ED': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE150000003ADD': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1600000027EC': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE150000003AD4': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002E0C': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1600000024EE': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE1600000025B1': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE1600000025AE': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE150000002CE7': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002CED': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002DD0': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002CE4': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002DB4': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002CB4': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002E07': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000003AE4': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000003AEE': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000003ADA': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000003AE7': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000003A97': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000003AEA': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000003AD3': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000003ADF': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000003AE5': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002DB7': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002C38': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1600000027F2': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE1600000027F0': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE1600000027DC': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE150000003AF0': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000003AD9': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000003ADE': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000003AB9': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000003ABB': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000003AC0': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000003ACB': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000003AC9': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000003AD1': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000003AD0': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE160000002384': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE160000002823': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE150000003AD6': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE160000002378': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE1600000027DE': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE16000000280C': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE150000003ACA': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000003ACF': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000003AB6': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000003ABE': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000003AB3': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000003ABD': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000003AD5': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000003ADC': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000003AE0': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000003AC1': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000003AC6': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000003AD2': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000003AC7': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000003AD7': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000003ABF': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000003ACC': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000003AAA': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000003AA5': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000003A9B': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000003AF3': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000003A9F': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000003ABC': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000003AB4': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000003AC8': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000003ADB': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000003ACE': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000003AC3': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000003AC5': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000003A94': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000003AAB': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000003AB8': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000003AAE': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000003AB0': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000003AF4': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000003AF2': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000003A98': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000003AC2': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000003A9A': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000003AB7': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000003ACD': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000003AAC': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000003AB1': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000003A9C': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000003A96': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000003AA0': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000003AB5': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000003A99': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000003AA6': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000003AA8': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000003AA9': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000003AAD': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002360': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002523': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000023AE': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000003AA7': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE16000000280B': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE150000003AA2': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000003AE1': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE160000002808': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE150000003AED': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000003AAF': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000003AF1': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE160000002807': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE160000002816': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE160000002822': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE1600000027F3': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE160000002805': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE160000002411': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE150000003A9D': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1600000023C0': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE1600000023A5': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE150000003AA3': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002341': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000019EF': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000003AB2': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000003AEC': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000017E2': {'fwver': '1050400', 'hwver': 0x24},
        'D91E150000003AE3': {'fwver': 'None', 'hwver': None},
        'D9AE150000003AE3': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000003AF7': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000003AF9': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000003AF8': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000003AF5': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000003AE8': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000003A9E': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000003AE9': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000001839': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE15000000155F': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE150000001342': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE150000001838': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE1500000015FC': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE150000001464': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE150000001352': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE150000001846': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE15000000185A': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE150000001361': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE15000000181F': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE1500000014BC': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE150000001725': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE150000001877': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE150000001867': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE150000001969': {'fwver': 'None', 'hwver': None},
        'D9AE1500000014E8': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE1500000012CA': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE150000002D8B': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000001447': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE1600000027E0': {'fwver': 'FC050600', 'hwver': 0x34},
        'D9AE150000003A59': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000003A60': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000003A58': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000003A5D': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000003A5A': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000003A45': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000003A57': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000003A5F': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000003A4B': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000003A56': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000003A4F': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000003A53': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000003A54': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000003A5E': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000003A63': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000003A4C': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000003A62': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000003A3C': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000003A43': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000003A41': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE15000000160D': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE15000000161C': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE1500000013F3': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE15000000134F': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE150000001356': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE150000001795': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE150000002412': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000001850': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE1500000015ED': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE150000001425': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE15000000183E': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE150000001748': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE1500000017B0': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE15000000173F': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE1500000015FD': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE15000000162D': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE150000002E14': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE15000000180C': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE150000001761': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE150000002DDD': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000001848': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE1500000015EB': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE150000001744': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE1500000013D8': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE150000001309': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE150000001562': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE1500000015F9': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE1500000015E6': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE150000001557': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE150000003A46': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE15000000135A': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE150000001312': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE1500000015E7': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE15000000161F': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE15000000185C': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE150000002E36': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE15000000173E': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE15000000185E': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE150000002E39': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002DC6': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002CA9': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002CCE': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002E2F': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE15000000171E': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE150000002E1C': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002CAF': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002E28': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002D9E': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002CE0': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002E27': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002CCF': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE15000000162C': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE150000001816': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE150000001466': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE15000000172C': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE15000000168B': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE1500000014F5': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE15000000172A': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE150000001446': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE1500000012D8': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE150000001481': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE150000002CC6': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000023FE': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000001583': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE150000002E21': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000016F8': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE15000000161E': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE150000001783': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE150000002CC0': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002E25': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000015BE': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE150000002CE5': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000015E4': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE150000001569': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE15000000176D': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE150000002371': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000001603': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE1500000017AF': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE150000002E18': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002D13': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002CCD': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE15000000177E': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE150000002E11': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002E15': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE15000000249C': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002338': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002E0B': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002D66': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002E05': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000024FE': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000015AA': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE15000000252F': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE15000000251E': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002549': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002526': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000015D9': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE150000002CAD': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002CE9': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002E0E': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002519': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002CE6': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002562': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002520': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000024D9': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002CEC': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000025A3': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE15000000258D': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000001471': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE15000000146E': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE15000000250A': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000024BD': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002508': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000015FA': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE15000000250F': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000013BC': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE15000000252A': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002571': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002464': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE15000000259E': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002531': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000025D7': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE15000000257C': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE15000000252D': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000024C3': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE15000000182D': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE1500000024F2': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000025C4': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000024C9': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000024B3': {'fwver': 'None', 'hwver': None},
        'D9AE150000002564': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000001728': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE1500000024DB': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000001775': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE15000000254D': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE15000000171B': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE15000000254C': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000025D3': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE15000000147C': {'fwver': '1050400', 'hwver': 0x24},
        'D9AE15000000259F': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002546': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002527': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000024B8': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000024BC': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE150000002518': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1500000024DA': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE15000000235A': {'fwver': 'None', 'hwver': None},
        'D9AE15000000256B': {'fwver': 'None', 'hwver': None},
        'D9AE150000002482': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE160000003280': {'fwver': '01010D04', 'hwver': 0x53},
        'D9AE16000000325C': {'fwver': '01010D04', 'hwver': 0x53},
        'D9AE160000003247': {'fwver': '01010D04', 'hwver': 0x53},
        'D9AE16000000324C': {'fwver': '01010D04', 'hwver': 0x53},
        'D9AE1600000032AB': {'fwver': '01010D04', 'hwver': 0x53},
        'D9AE16000000315F': {'fwver': '01010D04', 'hwver': 0x53},
        'D9AE160000003302': {'fwver': '01010D04', 'hwver': 0x53},
        'D9AE160000003356': {'fwver': '01010D04', 'hwver': 0x53},
        'D9AE160000003260': {'fwver': '01010D04', 'hwver': 0x53},
        'D9AE160000003354': {'fwver': '01010D04', 'hwver': 0x53},
        'D9AE160000003268': {'fwver': '01010D04', 'hwver': 0x53},
        'D9AE16000000326A': {'fwver': '01010D04', 'hwver': 0x53},
        'D9AE160000003242': {'fwver': '01010D04', 'hwver': 0x53},
        'D9AE1600000032DC': {'fwver': '01010D04', 'hwver': 0x53},
        'D9AE160000003344': {'fwver': '01010D04', 'hwver': 0x53},
        'D9AE1600000032D7': {'fwver': '01010D04', 'hwver': 0x53},
        'D9AE16000000324F': {'fwver': '01010D04', 'hwver': 0x53},
        'D9AE16000000324E': {'fwver': '01010D04', 'hwver': 0x53},
        'D9AE160000003158': {'fwver': '01010D04', 'hwver': 0x53},
        'D9AE160000003298': {'fwver': '01010D04', 'hwver': 0x53},
        'D9AE16000000332B': {'fwver': '01010D04', 'hwver': 0x53},
        'D9AE1600000032C1': {'fwver': '01010D04', 'hwver': 0x53},
        'D9AE16000000318C': {'fwver': '01010D04', 'hwver': 0x53},
        'D9AE16000000315B': {'fwver': '01010D04', 'hwver': 0x53},
        'D9AE1600000031F8': {'fwver': '01010D04', 'hwver': 0x53},
        'D9AE160000003287': {'fwver': '01010D04', 'hwver': 0x53},
        'D9AE1600000032AE': {'fwver': '01010D04', 'hwver': 0x53},
        'D9AE16000000324D': {'fwver': '01010D04', 'hwver': 0x53},
        'D9AE16000000324B': {'fwver': '01010D04', 'hwver': 0x53},
        'D9AE1600000032A5': {'fwver': '01010D04', 'hwver': 0x53},
        'D9AE160000003215': {'fwver': '01010D04', 'hwver': 0x53},
        'D9AE16000000318B': {'fwver': '01010D04', 'hwver': 0x53},
        'D9AE160000003185': {'fwver': '01010D04', 'hwver': 0x53},
        'D9AE160000003281': {'fwver': '01010D04', 'hwver': 0x53},
        'D9AE160000003217': {'fwver': '01010D04', 'hwver': 0x53},
        'D9AE16000000328A': {'fwver': '01010D04', 'hwver': 0x53},
        'D9AE16000000327A': {'fwver': '01010D04', 'hwver': 0x53},
        'D9AE1600000031F6': {'fwver': '01010D04', 'hwver': 0x53},
        'D9AE16000000328E': {'fwver': '01010D04', 'hwver': 0x53},
        'D9AE160000003288': {'fwver': '01010D04', 'hwver': 0x53},
        'D9AE160000003289': {'fwver': '01010D04', 'hwver': 0x53},
        'D9AE160000003272': {'fwver': '01010D04', 'hwver': 0x53},
        'D9AE160000003303': {'fwver': '01010D04', 'hwver': 0x53},
        'D9AE1600000031F4': {'fwver': '01010D04', 'hwver': 0x53},
        'D9AE1600000031A6': {'fwver': '01010D04', 'hwver': 0x53},
        'D9AE16000000327F': {'fwver': '01010D04', 'hwver': 0x53},
        'D9AE16000000320F': {'fwver': '01010D04', 'hwver': 0x53},
        'D9AE1600000031FD': {'fwver': '01010D04', 'hwver': 0x53},
        'D9AE1600000032B7': {'fwver': '01010D04', 'hwver': 0x53},
        'D9AE150000002379': {'fwver': 'FC050600', 'hwver': 0x24},
        'D9AE1600000031A3': {'fwver': '01010D04', 'hwver': 0x53},
        'D9AE1600000031C7': {'fwver': '01010D04', 'hwver': 0x53},
        'D9AE160000003209': {'fwver': '01010D04', 'hwver': 0x53},
        'D9AE1600000031B8': {'fwver': '01010D04', 'hwver': 0x53},
        'D9AE1600000032E6': {'fwver': '01010D04', 'hwver': 0x53},
        'D9AE1600000032B0': {'fwver': '01010D04', 'hwver': 0x53},
        'D9AE160000003295': {'fwver': '01010D04', 'hwver': 0x53},
        'D9AE1600000031B9': {'fwver': '01010D04', 'hwver': 0x53},
        'D9AE160000003249': {'fwver': '01010D04', 'hwver': 0x53},
        'D9AE16000000316A': {'fwver': '01010D04', 'hwver': 0x53},
        'D9AE16000000332F': {'fwver': '01010D04', 'hwver': 0x53},
        'D9AE160000003312': {'fwver': '01010D04', 'hwver': 0x53},
        'D9AE160000003269': {'fwver': '01010D04', 'hwver': 0x53},
        'D9AE160000003176': {'fwver': '01010D04', 'hwver': 0x53},
        'D9AE1600000031BF': {'fwver': '01010D04', 'hwver': 0x53},
        'D9AE1600000031E6': {'fwver': '01010D04', 'hwver': 0x53},
        'D9AE160000003284': {'fwver': '01010D04', 'hwver': 0x53},
        'D9AE16000000331C': {'fwver': '01010D04', 'hwver': 0x53},
        'D9AE16000000331D': {'fwver': '01010D04', 'hwver': 0x53},
        'D9AE160000003169': {'fwver': '01010D04', 'hwver': 0x53},
        'D9AE16000000315D': {'fwver': '01010D04', 'hwver': 0x53},
        'D9AE160000003286': {'fwver': '01010D04', 'hwver': 0x53},
        'D9AE1600000031A1': {'fwver': '01010D04', 'hwver': 0x53},
        'D9AE160000003311': {'fwver': '01010D04', 'hwver': 0x53},
        'D9AE1600000031F9': {'fwver': '01010D04', 'hwver': 0x53},
        'D9AE160000003171': {'fwver': '01010D04', 'hwver': 0x53},
        'D9AE160000003172': {'fwver': '01010D04', 'hwver': 0x53},
        'D9AE160000003331': {'fwver': '01010D04', 'hwver': 0x53},
        'D9AE1600000031EE': {'fwver': '01010D04', 'hwver': 0x53},
        'D9AE1600000031FF': {'fwver': '01010D04', 'hwver': 0x53},
        'D9AE16000000320C': {'fwver': '01010D04', 'hwver': 0x53},
        'D9AE1600000031DC': {'fwver': '01010D04', 'hwver': 0x53},
        'D9AE1600000031A0': {'fwver': '01010D04', 'hwver': 0x53},
        'D9AE160000003162': {'fwver': '01010D04', 'hwver': 0x53},
        'D9AE160000003198': {'fwver': '01010D04', 'hwver': 0x53},
        'D9AE160000003283': {'fwver': '01010D04', 'hwver': 0x53},
        'D9AE160000003296': {'fwver': 'None', 'hwver': None},
        'D9AE160000003160': {'fwver': '01010D04', 'hwver': 0x53},
        'D9AE16000000323F': {'fwver': '01010D04', 'hwver': 0x53},
        'D9AE1600000032B8': {'fwver': '01010D04', 'hwver': 0x53},  # both were None
    }


    hwverdict = {
        0x23: "Gen2",
        0x24: "Gen2",
        0x31: "Gen2",
        0x33: "Gen2",
        0x34: "Gen2",
        0x40: "Gen3",
        0x41: "Gen3",
        0x42: "Gen3",
        0x43: "Gen3",
        0x44: "Gen3",
        0x45: "Gen3",
        0x46: "Gen3",
        0x50: "Gen3",
        0x51: "Gen3",
        0x52: "Gen3",
        0x53: "Gen3",
        0x54: "Gen3",
        0x61: "Gen3",
        0x62: "Gen3",
    }

    @property
    def HWVersion(self):
        if self.hwver == None:
            return "Unknown Tag"
        return TagUID.hwverdict[self.hwver]

    def __init__(self,uuidstr):
        # Tag UUID format D9AE150000012345 16*4 = 64bits
        # GS1CompanyPrefix16 = uuidstr[0:4]
        # sernum = uuidstr[11:]
        self.uid = uuidstr
        if uuidstr == None:
            foo = 3
        typestr = uuidstr[4:6]
        typeid = int(typestr, 16)
        if uuidstr in TagUID.hwdb:
            self.hwver = TagUID.hwdb[uuidstr]['hwver']
            self.fwver = TagUID.hwdb[uuidstr]['fwver']
        else:
            self.hwver = None
            self.fwver = None
        self.tagtype = self.ProductType(typeid)

    def __str__(self):
        retval = str(self.tagtype)
        if retval[12:16] == 'VIEW':
            retval = retval[12:17]

        return f"{retval}({self.HWVersion})"



    class ProductType(Enum):
        ReservedForFutureUse = 0x00
        POWER400 = 0x01
        VIEW2 = 0x02
        VIEW3_Gen1 = 0x03
        VIEW4_Gen1 = 0x04
        VIEW3_Gen1_Button = 0x05
        VIEW4_Gen1_Button = 0x06
        POWER400X = 0x07
        VIEW3_Gen1_5 = 0x08
        VIEW3_Gen1_5_Button = 0x09
        VIEW3_Gen2_External_Power = 0x0A
        VIEW4_Gen2_External_Power = 0x0B
        VIEW4_Gen1_5 = 0x10
        VIEW4_Gen1_5_Button = 0x11
        VIEW3_Gen2 = 0x13
        VIEW4_Gen2 = 0x14
        VIEW3_Gen2_Accessories = 0x15  # VIEW3_Gen3_compatible_with_Gen2 3inch
        VIEW4_Gen2_Accessories = 0x16  # VIEW3_Gen3_compatible_with_Gen2 4inch
        Mobile_Link_Gateway = 0x17
        Network_Link_Gateway = 0x18
        VIEW10_Gen1 = 0x1A
        VIEW10_Gen1_5_MPico = 0x1B
        VIEW10_Gen2 = 0x1C
        Any_IEEE_protocol_tag = 0x1D
        POWER_60 = 0x1E
        POWER_100 = 0X1F
        VIEW10_Gen1_75Mpico_Gainspan_3_IR_Sensors = 0x20
        VIEW10_Gen1_25 = 0x21
        VIEW3_Gen3 = 0x23
        VIEW4_Gen3 = 0x24
        VIEW7_Gen3 = 0x27

class LogTime(datetime.datetime):
    def __new__(cls, timestr):
        time = strptime(timestr, '%Y-%m-%d %H:%M:%S')
        # self.time = datetime.datetime(year=self.time.tm_year, month=self.time.tm_mon, day=self.time.tm_mday,
        #                               hour=self.time.tm_hour, minute=self.time.tm_min, second=self.time.tm_sec)
        # super().__init__(self.time)

        return datetime.datetime.__new__(cls, time.tm_year, time.tm_mon, time.tm_mday,
                                      time.tm_hour, time.tm_min, time.tm_sec)

    def __init__(self, timestr):
        self.timestr = timestr
        # self.time = strptime(timestr,'%Y-%m-%d %H:%M:%S.%f')
        # self.time = datetime.datetime(year=self.time.tm_year, month=self.time.tm_mon, day=self.time.tm_mday, hour=self.time.tm_hour, minute=self.time.tm_min, second=self.time.tm_sec)
        # super().__init__(self.time)
        foo = 3

    # def __str__(self):
    #     return strftime('%Y-%m-%d %H:%M:%S', self.time)
    #
    # def __rsub__(self,value):
    #     return self.time - value

class TagUpdateStats():
    def __init__(self):
        self._outputfile = sys.stdout
        self.warnonly = False

    def mock_write(self, text):
        with open(self.outputfile, "a") as fh:
            fh.write(text)
        real_write = type(sys.stdout).write
        real_write(sys.stdout, text)

    def OpenLogfilesFromZipFile(self, zipfilename='ServerHost.zip'):
        assert(zipfilename)
        with ZipFile(zipfilename, mode='r') as zipfile:
            # zipfile.printdir()
            # filename = zipfilename
            # basename = splitext(zipfilename)[0]
            for file in zipfile.filelist:
                extension = splitext(file.filename)[1]
                if extension == '.log':
                    # print(file.filename)
                    yield zipfile.open(file)

    def main(self, argv):
        inputfile = None
        tracefile = None
        outputfile = 'stdout'
        zipfile = None

        def usage(prog):
            print('{} (-z <ServerHost.zip>) (-o) <outputfile>'.format(prog))

        try:
            opts, args = getopt.getopt(argv[1:], "hwz:o:")
        except getopt.GetoptError:
            usage(f"{argv[0]}")
            sys.exit(1)

        # if len(args) > 1:
        #     usage(f"{argv[0]}")
        #     sys.exit(1)

        for opt, arg in opts:
            if opt == '-h':
                usage(f"{argv[0]}")
                sys.exit(2)
            elif opt == '-z':
                zipfile = arg
            elif opt == '-w': # warn only
                self.warnonly = True
            elif opt == '-o':
                self.outputfile, outputfile = arg, arg
                with open(outputfile, "w") as fh: pass # truncate the file
                sys.stdout.write = self.mock_write  # decode to both stdout and outputfile
        # if inputfile: print('Input file is "{}"'.format(inputfile if inputfile else 'stdin'))
        # if tracefile: print('Trace file is "{}"'.format(tracefile if tracefile else 'stdin'))
        print('Input file is "{}"'.format(zipfile))
        print('Output file is "{}"'.format(outputfile))

        for arg in args:
            print("arg:",arg)

        TagUpdateDict = SortedDict()
        TagTemplateDataDict = SortedDict()
        starttime=None
        endtime=None
        updateidx = 0
        linenum=0

        if zipfile:
            for logfile in self.OpenLogfilesFromZipFile(zipfilename=zipfile):
                print(f"Processing log file: {logfile}")
                for line in logfile:
                    linenum += 1

                    grps = TemplateDataRegexCompiled.match(str(line, 'UTF-8'))
                    if grps:
                        uuid = grps.group('uuid')
                        endtime = LogTime(grps.group('time'))
                        if not starttime:
                            starttime = endtime

                        templatedatastr = grps.group('fielddata')#.encode('utf-8')
                        # if uuid != 'D9AE1600000027E9':
                        #     continue
                        # check to see if it what we care about
                        if not FieldRegexCompiled.match(templatedatastr):
                            continue

                        templatedatahash = hashlib.sha256(templatedatastr.encode('utf-8')).hexdigest()
                        if uuid not in TagTemplateDataDict:
                            TagTemplateDataDict[uuid] = {
                                'numdatasets':0,
                                'rawfielddatalen':0,
                                'optimizeddatalen':0,
                                'uniquedatasethashes':[],
                                'tagupdates':0,
                                'fieldshashes':SortedDict()
                            }

                        TagTemplateDataDict[uuid]['tagupdates'] += 1

                        if templatedatahash not in TagTemplateDataDict[uuid]['uniquedatasethashes']:
                            # print(templatedata)
                            # if uuid == 'D9AE160000003129':
                            #     print(uuid, templatedatahash, templatedata)
                            TagTemplateDataDict[uuid]['uniquedatasethashes'].append(templatedatahash)
                            # TagTemplateDataDict[uuid]['uniquefielddatahashes']=[]
                            # Check if field data is unique
                            # templatedatastr = str(templatedata, 'UTF-8')
                            # print(templatedatastr)
                            fielditer = FieldRegexCompiled.finditer(templatedatastr)
                            datapresent = False
                            updaterawbytes = 0
                            for grp in fielditer:
                                fielddata = grp.group('data')
                                updaterawbytes += len(fielddata)
                                TagTemplateDataDict[uuid]['rawfielddatalen'] = len(fielddata) + TagTemplateDataDict[uuid]['rawfielddatalen']
                                fieldnum = grp.group('fieldnum')
                                if (len(fielddata)==0) or FieldDataBlankCompiled.match(fielddata):
                                    TagTemplateDataDict[uuid]['fieldshashes'][fieldnum]=[]
                                    foo = 3
                                    # print('blank')
                                    # print(":".join("{:02x}".format(ord(c)) for c in fielddata))
                                else:
                                    # fielddataencoded = fielddata.encode('utf-8')
                                    # fielddatahash = hashlib.sha256(fielddataencoded).hexdigest()
                                    fielddatahash = fielddata

                                    if fieldnum not in TagTemplateDataDict[uuid]['fieldshashes']:
                                        TagTemplateDataDict[uuid]['fieldshashes'][fieldnum] = []
                                    if fielddatahash not in TagTemplateDataDict[uuid]['fieldshashes'][fieldnum]:
                                        TagTemplateDataDict[uuid]['fieldshashes'][fieldnum].append(fielddatahash)
                                        # bar = fielddata.encode('utf-8')
                                        # foo = zlib.compress(bar,level=9)
                                        # print(len(bar), len(foo))
                                        TagTemplateDataDict[uuid]['optimizeddatalen'] = len(fielddata) + TagTemplateDataDict[uuid][
                                            'optimizeddatalen']

                                        foo = 3
                                # print(fielddata)
                                datapresent = True
                            updateidx += 1
                            updaterawbytes += len(fielddata)
                            TagUpdateDict[updateidx] = {
                                'time': endtime,
                                'uuid':uuid,
                                'numbytes':updaterawbytes
                            }
                            if not datapresent:
                                foo = 3
                            assert(datapresent)

                        TagTemplateDataDict[uuid]['numdatasets'] = TagTemplateDataDict[uuid]['numdatasets'] + 1
                        # TagTemplateDataDict[uuid]['uniquefielddatahashes'].append([])

                        # print( grps[1], grps[2])
                        #print(line)

            print("Number of tags sent template data: ", len(TagTemplateDataDict))
            print("                               +---- total data sets)")
            print("                               |  +- unique data sets (unique screen states")
            print("      UUID         type        v  v  bytes  bytes(opt) BPU  BPU(optimzed)    Field# unique values (not including blanks)")
            totalraw = 0
            totaloptimized = 0
            totaltagupdates = 0
            for uuid, templatedataentires in TagTemplateDataDict.items():
                totalraw += templatedataentires['rawfielddatalen']
                totaloptimized += templatedataentires['optimizeddatalen']
                totaltagupdates += templatedataentires['tagupdates']
                print("{} {}  {:2} {:2} {:4}     {:4}     {:4}    {:4}           {}".format(
                    uuid,
                    TagUID(uuid),
                    templatedataentires['numdatasets'],
                    len(templatedataentires['uniquedatasethashes']),
                    templatedataentires['rawfielddatalen'],
                    templatedataentires['optimizeddatalen'],
                    int(templatedataentires['rawfielddatalen']/templatedataentires['tagupdates']),
                    int(templatedataentires['optimizeddatalen']/templatedataentires['tagupdates']),
                    "  ".join("field{:>02}:{:>02}".format(key, len(val)) for key, val in templatedataentires['fieldshashes'].items())
                    # len(templatedataentires['uniquefielddatahashes'])
                    )
                )
            print("Totals{:21}    {}            avg({}) avg({})          {:.3g}% reduction from caching".format(
                totalraw,
                totaloptimized,
                int(totalraw/totaltagupdates),
                int(totaloptimized/totaltagupdates),
                (totalraw-totaloptimized)/totalraw*100)
            )
            # for line in self.ReadLogfileFromZipFile(zipfilename=zipfi
            # re.match(regexstr, itemname)
            duration = endtime-starttime
            print(f"duration of capture: {duration}")
            print(f"field data bit-rate(bits per second): {int(totalraw*8/duration.seconds)}")

            atime = TagUpdateDict[1]['time']
            btime = atime
            bytessubtotal = 0
            updatesubtotal = 0
            maxrate = 0
            maxupdates = 0
            numentries = len(TagUpdateDict.items())
            for idx, update in TagUpdateDict.items():
                curtime = update['time']
                delta = curtime-atime
                if delta.seconds > 3:
                    atime = curtime
                    btime = curtime
                    rate = int(bytessubtotal*8/3)
                    if rate > maxrate:
                        maxrate = rate
                    if updatesubtotal > maxupdates:
                        maxupdates = updatesubtotal
                    print(f"{update['time']}  {update['numbytes']} maxupdates={updatesubtotal} byterate={int(rate/3)}")
                    bytessubtotal = update['numbytes']
                    updatesubtotal = 1
                else:
                    print(f"{update['time']}  {update['numbytes']}")
                    bytessubtotal += update['numbytes']
                    updatesubtotal += 1
                    btime = curtime
                    continue


                # print(delta.seconds)
                # print(f"{update['time']}  {update['uuid']} {update['numbytes']}")

                foo = 3

            print(f"max updates in 3 second period={maxupdates}, max byte-rate in 3 second period: {int(maxrate/3)}")
            foo = 3

class TagFlipIntegrityStats():
    def __init__(self):
        self._outputfile = sys.stdout
        self.warnonly = False

    def mock_write(self, text):
        with open(self.outputfile, "a") as fh:
            fh.write(text)
        real_write = type(sys.stdout).write
        real_write(sys.stdout, text)

    def OpenLogfilesFromZipFile(self, zipfilename='ServerHost.zip'):
        assert(zipfilename)
        with ZipFile(zipfilename, mode='r') as zipfile:
            # zipfile.printdir()
            # filename = zipfilename
            # basename = splitext(zipfilename)[0]
            for file in zipfile.filelist:
                extension = splitext(file.filename)[1]
                if extension == '.log':
                    # print(file.filename)
                    yield zipfile.open(file)

    def main(self, argv):
        outputfile = 'stdout'
        zipfile = None
        logiscent = None
        tag = None
        reportrssistats = None
        reportrssistatsfailedonly = None
        reportcommandfailedonly = None
        reportcommandretriesonly = None
        reportcommandsall = None
        reporttaggatewayaffiliation = None
        reporttaggatewayaffiliationforfailedcommands = None
        reportgatewaytagaffiliation = None
        reportgatewaytagaffiliationreportalltags = None
        linenum=0

        def usage(prog):
            print('''
            {prog} [-z <ServerHost.zip>] [-g <gateway ip of interest>] [-t <tag uid>] [-o <outputfile>])
            -a = report tag gateway affiliation for failed tag commands
            -A = report tag gateway affiliation for all tags
            -z = use zip file of logs and report on all files contained within.
            -t = focus on this tag
            -R = report RSSI status for all tags.
            -r = report RSSI status for only failed tags
            -C = report all tag commands failures
            -c = report only failed tag commands
            -d = report only tags with command retries
            -G = Report a list of tags that have affiliated with each gateway

            -
            
            
            ''')

        try:
            opts, args = getopt.getopt(argv[1:], "aACcdgGhL:wz:o:Rrt:")
        except getopt.GetoptError:
            usage(f"{argv[0]}")
            sys.exit(1)

        # if len(args) > 1:
        #     usage(f"{argv[0]}")
        #     sys.exit(1)



        for opt, arg in opts:
            if opt == '-a':
                reporttaggatewayaffiliationforfailedcommands = True
            elif opt == '-A':
                reporttaggatewayaffiliation = True
            elif opt == '-G':
                reportgatewaytagaffiliation = True
                reportgatewaytagaffiliationreportalltags = True
            elif opt == '-g':
                reportgatewaytagaffiliation = True
            elif opt == '-c':
                reportcommandfailedonly = True
            elif opt == '-C':
                reportcommandsall = True
            elif opt == '-d':
                reportcommandretriesonly = True
            elif opt == '-h':
                usage(f"{argv[0]}")
                sys.exit(2)
            elif opt == '-z':
                zipfile = arg
            elif opt == '-w':  # warn only
                self.warnonly = True
            elif opt == '-o':
                self.outputfile, outputfile = arg, arg
                with open(outputfile, "w") as fh:
                    pass  # truncate the file
                sys.stdout.write = self.mock_write  # decode to both stdout and outputfile
            elif opt == '-L':
                logiscend = arg
            elif opt == '-R':
                reportrssistats = True
            elif opt == '-r':
                reportrssistatsfailedonly = True
            elif opt == '-t':
                tag = arg
        # if inputfile: print('Input file is "{}"'.format(inputfile if inputfile else 'stdin'))
        # if tracefile: print('Trace file is "{}"'.format(tracefile if tracefile else 'stdin'))
        print('Input file is "{}"'.format(zipfile))
        print('Output file is "{}"'.format(outputfile))

        for arg in args:
            print("arg:",arg)

        if zipfile:
            for logfile in self.OpenLogfilesFromZipFile(zipfilename=zipfile):
                print(f"Processing log file: {logfile.name}")
                if reportrssistatsfailedonly or reportrssistats:
                    serviceAnnouncementLogger = ServiceAnnouncementLogger()

                if reportrssistatsfailedonly or reportcommandsall or reportcommandretriesonly or reportcommandfailedonly or reporttaggatewayaffiliationforfailedcommands:
                    reportcommandstatus = ReportCommandStatus(tagsofinterest=trimandfoamtags)


                if reporttaggatewayaffiliation or reporttaggatewayaffiliationforfailedcommands or reportgatewaytagaffiliation:
                    reportTagGatewayAffiliation = ReportTagGatewayAffiliation()
                # if reportcommandsall or reportcommandfailedonly:
                #     reportTagCommunicationuml = ReportTagCommunicationUML()
                # report tag gateway affinity XXXTODO

                failedUUIDs = None
                tagsofinterest = None

                for line in logfile:
                    linenum += 1
                    if reportrssistatsfailedonly or reportrssistats:
                        serviceAnnouncementLogger.Log(line, linenum=linenum)
                    if reportcommandsall or reportrssistatsfailedonly or reportcommandretriesonly or reportcommandfailedonly or reporttaggatewayaffiliationforfailedcommands:
                        reportcommandstatus.Log(line, linenum=linenum)
                    if reporttaggatewayaffiliation or reporttaggatewayaffiliationforfailedcommands or reportgatewaytagaffiliation:
                        reportTagGatewayAffiliation.Log(line, linenum=linenum)
                    # reportTagCommunicationuml.Log(line, linenum=linenum)

                if reportrssistatsfailedonly or reportcommandfailedonly or reporttaggatewayaffiliationforfailedcommands:
                    failedUUIDs = reportcommandstatus.GetTagFailuresUUIDlist()

                if reportcommandsall:
                    if tag:
                        print(f'Reporting status of all commands to {tag} only')
                        reportcommandstatus.Report(tagsofinterest=[tag])
                    else:
                        print('Reporting status of all commands to all tags')
                        reportcommandstatus.Report(tagsofinterest=None)
                elif reportcommandretriesonly:
                    if tag:
                        print(f'Reporting status of commands to {tag} with retries')
                        reportcommandstatus.ReportRetries(tagsofinterest=[tag])
                    else:
                        print('Reporting status of all tags with retries')
                        reportcommandstatus.ReportRetries(tagsofinterest=None)
                elif reportcommandfailedonly:
                    if failedUUIDs:
                        if tag:
                            print(f'Reporting failed commands for {tag} only')
                            reportcommandstatus.ReportFailures(tagsofinterest=[tag])
                        else:
                            print('Reporting failed commands for all tag')
                            reportcommandstatus.ReportFailures(tagsofinterest=None)


                if reportrssistats:
                    if tag:
                        print(f'Reporting tag announces and RSSI levels for {tag} only')
                        serviceAnnouncementLogger.Report(filteronly=[tag])
                    else:
                        print('Reporting tag announces and RSSI levels')
                        serviceAnnouncementLogger.Report(filteronly=trimandfoamtags)
                elif reportrssistatsfailedonly:
                    print('Reporting tag announces and RSSI levels for failed tags only')
                    serviceAnnouncementLogger.Report(filteronly=failedUUIDs)

                if reporttaggatewayaffiliation:
                    if tag:
                        print(f'Reporting gateway affiliation for {tag}')
                        reportTagGatewayAffiliation.Report(filteronly=[tag])
                    else:
                        print('Reporting tag gateway affiliation')
                        reportTagGatewayAffiliation.Report(filteronly=None)
                elif reporttaggatewayaffiliationforfailedcommands:
                    if tag:
                        print(f'Reporting gateway affiliation for {tag} when commanding failed')
                        if failedUUIDs and len(failedUUIDs)>0 and tag in failedUUIDs:
                            reportTagGatewayAffiliation.Report(filteronly=[tag])
                        else:
                            reportTagGatewayAffiliation.Report(filteronly=[])
                    else:
                        print('Reporting tag gateway affiliations when commanding failed')
                        reportTagGatewayAffiliation.Report(filteronly=failedUUIDs)

                if reportgatewaytagaffiliation:
                    print('Reporting gateway tag affiliation')
                    reportTagGatewayAffiliation.ReportTagsAtGateways(listtags=reportgatewaytagaffiliationreportalltags, filteronly=trimandfoamtags)

                # serviceAnnouncementLogger.ReportUML(filteronly=failedUUIDs, title=str(failedUUIDs))
                # reportTagCommunicatio.ReportUML()

# 2021-06-02 10:10:52.6381|DEBUG|Panasonic.Hdk.Gateway.Internal.ToolService|167|Service Announce 10.16.220.212 TagUID: D9AE160000002823 Antenna 0 RSSI -47.00 Link 40 FreqOffSet -3 WakeUpReason 40 TimeStamp 2021-06-02 14:10:52 638 TxtPwr 13 MsgTyp 3 Sequence 35 RawData '30014020010222040000000F4E022710' Thread 167 |
class ServiceAnnouncementLogger():
    # doi = [
    #     'D9AE1600000031F9',
    #     'D9AE160000003171',
    #     'D9AE160000003172',
    #     'D9AE1600000031AD',
    #     'D9AE1600000031DC',
    #     'D9AE16000000320C'
    # ]
    def __init__(self, magfreqoffsetlimit=0, rssithreshold=0):
        self.magfreqoffsetlimit = magfreqoffsetlimit
        self.rssithreshold =rssithreshold
        serviceannounceRE = r'(?P<time>[0-9]{4}-[0-9]{2}-[0-9]{2}\s[0-9]{2}:[0-9]{2}:[0-9]{2}).*\s(?P<gateway>[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}).*(?P<uuid>[A-F0-9]{16})\sAntenna\s(?P<antenna>[0-9]+)\sRSSI\s(?P<rssi>-?[0-9]+\.[0-9]+).*Link\s(?P<link>[0-9]+).*FreqOffSet\s(?P<freqoffset>[-+]?[0-9]+)\sWakeUpReason\s(?P<wakeupreason>[0-9]+).*RawData\s\'(?P<rawdata>[A-F0-9]+)\''
        self.serviceannounceRECompiled = re.compile(serviceannounceRE)
        self.announcementdict = SortedDict()
        self.announceparser = AnnounceParser()
    def Log(self, line, linenum=None):
        linestr = str(line, 'UTF-8')
        grps = self.serviceannounceRECompiled.match(linestr)
        if grps:
            # self.announceparser.OnProcessRawHexData(hexstring=grps.group('rawdata'), linenum=linenum)
            magfreqoffset = abs(int(grps.group('freqoffset')))
            if magfreqoffset > self.magfreqoffsetlimit:
                uuid = grps.group('uuid')
                foo = TagUID(uuid).HWVersion
                # if TagUID(uuid).HWVersion != "Gen3":
                #     return # ignore
                time = grps.group('time')
                gateway = grps.group('gateway')
                # if gateway != '10.16.220.210':
                #     return
                uuid = grps.group('uuid')
                # if uuid not in ServiceAnnouncementLogger.doi:
                #     return
                antenna = grps.group('antenna')
                rssi = grps.group('rssi')
                if float(rssi) >= self.rssithreshold: ###################################################################
                    return
                link = grps.group('link')
                wakeupreason = grps.group('wakeupreason')
                freqoffset = grps.group('freqoffset')
                gateway = grps.group('gateway')
                newentry = {
                        'time':time,
                        'gateway':gateway,
                        'antenna':antenna,
                        'rssi':rssi,
                        'link':link,
                        'freqoffset':freqoffset,
                        'wakeupreason':wakeupreason,
                        'linenum':linenum
                        }
                if uuid in self.announcementdict:
                    self.announcementdict[uuid].append(newentry)
                else:
                    self.announcementdict[uuid] = [newentry]
    def CSVReport(self):
        print(f'Tag announces with |frequency offsets| greater than {self.magfreqoffsetlimit}')
        for uuid, list in self.announcementdict.items():
            for entry in list:
                header = 'uuid' + ''.join(", {}".format(key) for key in entry)
            break;
        print(header)
        for uuid, list in self.announcementdict.items():
            for entry in list:
                row = f"'{uuid}'" + ''.join(", {}".format(value) for key, value in entry.items())
            print(row)
    def Report(self, filteronly=None):
        print(f'Tag announces with |frequency offsets| greater than {self.magfreqoffsetlimit}')
        for uuid, list in self.announcementdict.items():
            for entry in list:
                if filteronly:
                    if uuid in filteronly:
                        print(uuid, TagUID(uuid), entry )
                else:
                    print(uuid, TagUID(uuid), entry)
        # report stats per gateway per tag
        TagGatewayStatsDict = SortedDict()
        for uuid, list in self.announcementdict.items():
            if 'D9AE1600000032E6' == uuid:
                foo = 2
            if filteronly and uuid not in filteronly: continue
            for entry in list:
                if uuid in TagGatewayStatsDict.keys():
                    if entry['gateway'] in TagGatewayStatsDict[uuid].keys():
                        TagGatewayStatsDict[uuid][entry['gateway']].append(float(entry['rssi']))
                    else:
                        # this gateway not recorded yet
                        TagGatewayStatsDict[uuid][entry['gateway']] = [float(entry['rssi'])]
                else:
                    # need to add a new entry
                    newentry = SortedDict()
                    newentry[entry['gateway']]=[float(entry['rssi'])]
                    TagGatewayStatsDict[uuid] = newentry
        print("Tag Gateway RSSI Stats ######################################################")
        print("UUID       Gateway     MinRSSI,  MaxRSSI,    AvgRSSI,  STDDEVRSSI")
        for uuid, entry in TagGatewayStatsDict.items():
            print(uuid, ':')
            for gateway, RSSIs in entry.items():
                minrssi = min(RSSIs)
                maxrssi = max(RSSIs)
                meanrssi = mean(RSSIs)
                stddevrssi = pstdev(RSSIs)
                print(f"         {gateway}  {minrssi: 6}    {maxrssi: 6}   {meanrssi:9.2f}    {stddevrssi:6.2f}")

    def ReportUML(self, filteronly=None, title="Untitled"):
        print(f'title {title}: Tag announces with |frequency offsets| greater than {self.magfreqoffsetlimit}')
        for uuid, list in self.announcementdict.items():
            for entry in list:
                if filteronly:
                    if uuid in filteronly:
                        print(
                            f"{uuid}->{entry['gateway']}: {entry['time']} antenna({entry['antenna']}) reason({entry['wakeupreason']} line({entry['linenum']})"
                        )
                else:
                    print(
                        f"{uuid}->{entry['gateway']}: {entry['time']} antenna({entry['antenna']}) reason({entry['wakeupreason']} line({entry['linenum']})"
                    )
        # report stats per gateway per tag
        TagGatewayStatsDict = SortedDict()
        for uuid, list in self.announcementdict.items():
            if 'D9AE1600000032E6' == uuid:
                foo = 2
            if filteronly and uuid not in filteronly: continue
            for entry in list:
                if uuid in TagGatewayStatsDict.keys():
                    if entry['gateway'] in TagGatewayStatsDict[uuid].keys():
                        TagGatewayStatsDict[uuid][entry['gateway']].append(float(entry['rssi']))
                    else:
                        # this gateway not recorded yet
                        TagGatewayStatsDict[uuid][entry['gateway']] = [float(entry['rssi'])]
                else:
                    # need to add a new entry
                    newentry = SortedDict()
                    newentry[entry['gateway']]=[float(entry['rssi'])]
                    TagGatewayStatsDict[uuid] = newentry
        print("Tag Gateway RSSI Stats ######################################################")
        print("UUID       Gateway    MinRSSI, MaxRSSI, AvgRSSI, STDDEVRSSI")
        for uuid, entry in TagGatewayStatsDict.items():
            print(uuid, ':')
            for gateway, RSSIs in entry.items():
                minrssi = min(RSSIs)
                maxrssi = max(RSSIs)
                meanrssi = mean(RSSIs)
                stddevrssi = pstdev(RSSIs)
                print(f"        {gateway}   {minrssi}    {maxrssi}   {meanrssi:.2f}    {stddevrssi:.2f}")



class ReportCommandStatus():
    def __init__(self, failthreshold=10, minthreshold=1, tagsofinterest=None):
        self.tagsofinterest = None
        self.failthreshold = failthreshold
        self.minthreshold = minthreshold
        # 2021-06-02 14:16:27.7191|INFO|Panasonic.Hdk.Gateway.Internal.CmdDispatcher|162|CmdDispatcher: SendCommand [0ms] Cmd: TagUID: 'D9AE16000000315B' Gtwy:Gateway(10.16.220.212) Rdr:-- ReqForAnnounce(TagPageFlipTotal, TagAwakeTimeTotal, Temperature, HardwareRev, BatteryLevel, FirmwareRev, ResetCount)[CID1252949] [CID1252949] Queued[XmitAttmpt0]|
        # (?P<uuid>[A-F0-9]{16}).*\((?P<gtwy>[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3})\).*\[(?P<cid>CID[0-9]{1,7})\].*XmitAttmpt0
        # CmdAttempregex = r'(?P<time>[0-9]{4}-[0-9]{2}-[0-9]{2}\s[0-9]{2}:[0-9]{2}:[0-9]{2}).*(SendCommand.*)?(?P<uuid>[A-F0-9]{16}).*Gtwy:(Gateway\()?(?P<gtwy>([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3})|\-\-)(\))?.*\[(?P<cid>CID[0-9]{1,7})\].*\[XmitAttmpt(?P<attemptNum>[0-9]{1,2})\]'
        #added 'Multiple' to only catch tag flips that fail.
        CmdAttempregex = r'(?P<time>[0-9]{4}-[0-9]{2}-[0-9]{2}\s[0-9]{2}:[0-9]{2}:[0-9]{2}).*(SendCommand.*)?(?P<uuid>[A-F0-9]{16}).*Gtwy:(Gateway\()?(?P<gtwy>([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3})|\-\-)(\))?.*Multiple.*\[(?P<cid>CID[0-9]{1,7})\].*\[XmitAttmpt(?P<attemptNum>[0-9]{1,2})\]'
        LEDCmdAttempregex = r'(?P<time>[0-9]{4}-[0-9]{2}-[0-9]{2}\s[0-9]{2}:[0-9]{2}:[0-9]{2}).*(SendCommand.*)?(?P<uuid>[A-F0-9]{16}).*Gtwy:(Gateway\()?(?P<gtwy>([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3})|\-\-)(\))?.*Multiple.*\[(?P<cid>CID[0-9]{1,7})\].*\[XmitAttmpt(?P<attemptNum>[0-9]{1,2})\]'
        self.CmdAttempregexCompiled = re.compile(CmdAttempregex)
        # this next one has the reliable gateway used
        executeSendingTagCmd = r'(?P<time>[0-9]{4}-[0-9]{2}-[0-9]{2}\s[0-9]{2}:[0-9]{2}:[0-9]{2}).*executeSendingTagCmd.*(?P<cid>CID[0-9]{1,7})\].*\[XmitAttmpt(?P<attemptNum>[0-9]{1,2})\].*(?P<uuid>[A-F0-9]{16}).*Gtwy:(Gateway\()?(?P<gtwy>([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3})|\-\-)(\))?.'
        self.executeSendingTagCmdCompiled = re.compile(executeSendingTagCmd)
        FailedAttemptRegex = r'(?P<time>[0-9]{4}-[0-9]{2}-[0-9]{2}\s[0-9]{2}:[0-9]{2}:[0-9]{2}).*\[(?P<cid>CID[0-9]{1,7})\].*Failed-TERM\[XmitAttmpt(?P<attemptNum>[10]{2})\]'
        self.FailedAttemptRegexCompiled = re.compile(FailedAttemptRegex)


        # 2021-06-15 13:41:37.7010|INFO|Panasonic.Hdk.Context.TagContext|63|DoExecute TagCmdContext(D9AE150000002045) - Multiple(TemplateData: [Text DataIndex:1 FldNum:0 Data:'                 ']TemplateData: [Text DataIndex:1 FldNum:1 Data:'                 ']TemplateData: [Text DataIndex:1 FldNum:2 Data:''])[CID2371627]|
        # 2021-06-15 13:41:37.8885|INFO|Panasonic.Hdk.Context.TagContext|173|DoExecute TagCmdContext(D9AE150000002CAF) - DisplayUpdate(PacketLength: 04 PageNumber: 01 TemplateIndex: 01 DataIndex: 01 Inverted: False AfterSleep: True)[CID2371608]|
        CMDRegEx = r'(?P<time>[0-9]{4}-[0-9]{2}-[0-9]{2}\s[0-9]{2}:[0-9]{2}:[0-9]{2}).*DoExecute (TagCmdContext|TagSleepContext).*(?P<uuid>[A-F0-9]{16}).*(?P<cmd>LEDControl\(Button\)|Multiple|DisplayUpdate|GPO\([0-9]?\)|KeepAwake\(100 msecs\)).*\[(?P<cid>CID[0-9]{1,7})\]'
        # CMDRegEx = r'(?P<time>[0-9]{4}-[0-9]{2}-[0-9]{2}\s[0-9]{2}:[0-9]{2}:[0-9]{2}).*(TagCmdContext|TagSleepContext|SendCommand).*(?P<uuid>[A-F0-9]{16}).*(?P<cmd>LEDControl\(Button\)|Multiple|DisplayUpdate|GPO\([0-9]?\)|KeepAwake\([\d]+ msecs\)|ReqForAnnounce).*\[(?P<cid>CID[0-9]{1,7})\]'
        self.CMDRegEx = re.compile(CMDRegEx)
        self.attemptdict = {}

    def Log(self, line, linenum=None):
        if grps := self.CMDRegEx.match(str(line, 'UTF-8')):
            cid = grps.group('cid')
            # if cid in self.attemptdict: return
            assert(cid not in self.attemptdict)
            assert(uuid := grps.group('uuid'))
            if self.tagsofinterest and (uuid not in self.tagsofinterest): return
            assert(time := grps.group('time'))
            assert(cmd := grps.group('cmd'))
            # attemptNum = grps.group('attemptNum')
            # gateway = grps.group('gtwy')
            self.attemptdict[cid] = {
                'uuid': uuid,
                'hwtype': TagUID(uuid).HWVersion,
                'time': time,
                'gtwy': None,
                'cmd':cmd,
                'lastattempt': None,
                'linenum': linenum,
                # 'failed':False
            }
        elif (grps := self.executeSendingTagCmdCompiled.match(str(line, 'UTF-8'))):
            cid = grps.group('cid')
            if cid not in self.attemptdict:
                foo = 3
                assert(time := grps.group('time'))
                assert (uuid := grps.group('uuid'))
                if self.tagsofinterest and (uuid not in self.tagsofinterest): return
                assert(attemptNum := grps.group('attemptNum'))
                assert(gateway := grps.group('gtwy'))
                self.attemptdict[cid] = {
                    'uuid': uuid,
                    'hwtype': TagUID(uuid).HWVersion,
                    'time': time,
                    'gtwy': gateway,
                    'cmd': None,
                    'lastattempt': attemptNum,
                    'linenum': linenum,
                    # 'failed': False
                }
            else:
                assert(cid in self.attemptdict)
                # assert(time := grps.group('time'))
                assert(attemptNum := grps.group('attemptNum'))
                assert(gateway := grps.group('gtwy'))
                self.attemptdict[cid]['gtwy']=gateway
                self.attemptdict[cid]['lastattempt']=attemptNum
                self.attemptdict[cid]['linenum']=linenum
        elif (grps := self.CmdAttempregexCompiled.match(str(line, 'UTF-8'))):
            cid = grps.group('cid')
            assert(cid in self.attemptdict)
            # time = grps.group('time')
            assert(attemptNum := grps.group('attemptNum'))
            self.attemptdict[cid]['lastattempt'] = attemptNum
        elif (grps := self.FailedAttemptRegexCompiled.match(str(line, 'UTF-8'))):
            cid = grps.group('cid')
            if cid not in self.attemptdict: return
            assert(cid in self.attemptdict)
            # time = grps.group('time')
            assert(attemptNum := grps.group('attemptNum'))
            self.attemptdict[cid]['lastattempt'] = attemptNum
            self.attemptdict[cid]['failed'] = True
            self.attemptdict[cid]['linenum'] = linenum

    def GetTagFailuresUUIDlist(self):
        retval = []
        for key, value in self.attemptdict.items():
            if lastval := value['lastattempt']:
                if int(lastval) == self.failthreshold:
                    tag = value['uuid']
                    if tag not in retval: retval.append(value['uuid'])
        return sorted(retval)

    def Report(self, tagsofinterest=None):
        numcmdswithretries = 0
        numcmdsfailed = 0
        for key, value in self.attemptdict.items():
            # if (value['uuid'] == 'D9AE1600000032E6'):
            #     print(key, value, '*************')
            if tagsofinterest and value['uuid'] not in tagsofinterest:
                continue

            if lastval := value['lastattempt']:
                if int(lastval) >= self.minthreshold:
                    numcmdswithretries += 1
                print(key, value)
        print(f"Number of commands with retries: {numcmdswithretries}")

        for key, value in self.attemptdict.items():
            if lastval := value['lastattempt']:
                if int(lastval) == self.failthreshold:
                    numcmdsfailed += 1
                    print(key, value)

        print(f"Number of commands with that totally failed: {numcmdsfailed}")

        if tagsofinterest:
            for tag in tagsofinterest:
                successgateways = {}
                for entry in self.attemptdict.values():
                    if 'failed' in entry.keys(): continue # only the good ones
                    uuid = entry['uuid']
                    if tag == uuid:
                        if gateway := entry['gtwy']:
                            if gateway in successgateways:
                                successgateways[gateway] += 1
                            else:
                                successgateways[gateway] = 1
                print(f"Successful gateways for {tag}({TagUID(tag).HWVersion}):")
                for gateway, count in successgateways.items():
                        print(f"    {gateway}({count})")

    def ReportRetries(self, tagsofinterest=None):
        numcmdswithretries = 0
        numcmdsfailed = 0
        for key, value in self.attemptdict.items():
            # if (value['uuid'] == 'D9AE1600000032E6'):
            #     print(key, value, '*************')
            if tagsofinterest and value['uuid'] not in tagsofinterest:
                continue

            if lastval := value['lastattempt']:
                if int(lastval) >= self.minthreshold:
                    numcmdswithretries += 1
                    print(key, value)
        print(f"Number of commands with retries: {numcmdswithretries}")

        # for key, value in self.attemptdict.items():
        #     if lastval := value['lastattempt']:
        #         if int(lastval) == self.failthreshold:
        #             numcmdsfailed += 1
        #             print(key, value)
        #
        # print(f"Number of commands with that totally failed: {numcmdsfailed}")

        if tagsofinterest:
            for tag in tagsofinterest:
                retrygateways = {}
                for entry in self.attemptdict.values():
                    if lastval := entry['lastattempt']:
                        if int(lastval) == 0: continue # skip any with retries
                    uuid = entry['uuid']
                    if tag == uuid:
                        if gateway := entry['gtwy']:
                            if gateway in retrygateways:
                                retrygateways[gateway] += 1
                            else:
                                retrygateways[gateway] = 1
                print(f"Retry gateways for {tag}({TagUID(tag).HWVersion}):")
                for gateway, count in retrygateways.items():
                        print(f"    {gateway}({count})")

    def ReportFailures(self, tagsofinterest=None):
        numcmdswithretries = 0
        numcmdsfailed = 0
        # for key, value in self.attemptdict.items():
        #     # if (value['uuid'] == 'D9AE1600000032E6'):
        #     #     print(key, value, '*************')
        #     if tagsofinterest and value['uuid'] not in tagsofinterest:
        #         continue
        #
        #     if lastval := value['lastattempt']:
        #         if int(lastval) >= self.minthreshold:
        #             numcmdswithretries += 1
        #             print(key, value)
        # print(f"Number of commands with retries: {numcmdswithretries}")

        for key, value in self.attemptdict.items():
            if value['uuid'] in tagsofinterest:
                if lastval := value['lastattempt']:
                    if int(lastval) == self.failthreshold:
                        numcmdsfailed += 1
                        print(key, value)
        print(f"Number of commands with that totally failed: {numcmdsfailed}")

        if tagsofinterest:
            for tag in tagsofinterest:
                failedgateways = {}
                for entry in self.attemptdict.values():
                    if 'failed' not in entry.keys(): continue # only the bad ones
                    uuid = entry['uuid']
                    if tag == uuid:
                        if gateway := entry['gtwy']:
                            if gateway in failedgateways:
                                failedgateways[gateway] += 1
                            else:
                                failedgateways[gateway] = 1
                print(f"Failed gateways for {tag}({TagUID(tag).HWVersion}):")
                for gateway, count in failedgateways.items():
                        print(f"    {gateway}({count})")




class GetHwVersionCmd():
    class GetHwVersion(ctypes.Structure):
        _pack_ = 1
        _fields_ = [
            ("cmdid", ctypes.c_uint8),
            ("len", ctypes.c_uint8),
            ("hwver", ctypes.c_uint8),
        ]
    def __init__(self, hwver=None):
        if hwver:
            self.cmd = GetHwVersionCmd.GetHwVersion(0x50, 1, hwver)
        else:
            self.cmd = GetHwVersionCmd.GetHwVersion()
        foobar = 3

    def Parse(self, offset, buffer):
        bufmv = memoryview(buffer)
        return offset+ctypes.sizeof(GetHwVersionCmd.GetHwVersion), GetHwVersionCmd.GetHwVersion.from_buffer(buffer[offset:])
# string_at(addressof(r),sizeof(r))
# dataSturct = Data(a=1, b=2, c=3)
# dataBytes = bytes(dataSturct)
# class GetHwVersion(ctypes.Structure):
#     _pack_ = 1
#     _fields_ = [
#         ("cmd", ctypes.c_uint8),
#         ("len", ctypes.c_uint8),
#         ("hwver", ctypes.c_uint8),
#     ]
#     def __init__(self, hwver):
#         # super().__init__(0x50, 1, hwver)
#         super().__init__(GetHwVersion.from_buffer(bytearray([1,2,3])))
#         # bar = ctypes.sizeof(self.cmd)
#         foo = 3


class AnnounceParser():
    class TAG_COMMANDS(Enum):
        ILLEGAL_TAG = 0x00
        FRAME_TOTAL = 0x01
        FRAME_NUMBER = 0x02
        ACK = 0x03
        NACK = 0x04
        DISPLAY_PAGE = 0x20
        GET_PAGE_LIST_COUNT = 0x21
        GET_SET_SLEEP_DWELL = 0x22
        GET_SET_AWAKE_DWELL_SECONDS = 0x23
        TEMPLATE_IMAGE_DRAW = 0x24
        GET_SET_ACK_DWELL_MILLISECONDS = 0x25
        GET_PAGE_LIST = 0x26
        GET_PAGE_CRC = 0x27
        DELETE_IMAGES = 0x28
        GET_SET_RETRY_DWELL = 0x29
        GET_SET_RETRY_COUNT = 0x2A
        GET_SET_LED_CONTROL_FLAGS = 0x2B
        STOP_RECEIVING = 0x2C
        GET_SET_BEACON_PERIOD = 0x2D
        GET_SET_EXT_BEACON_FLAGS = 0x2E
        GET_SET_EXT_BEACON_INTERVAL = 0x2F
        ANNOUNCE = 0x30
        GET_SET_RFID_EPC = 0x32
        REQUESTED_DATA = 0x33
        SAVE_TO_NVM = 0x34

        GET_SET_RF_CHANNEL = 0x40
        GET_SET_TX_POWER = 0x41
        GET_LAST_RX_RSSI = 0x43
        GET_BEACON_COUNT = 0x44
        GET_RFID_COUNT = 0x45
        GET_LAST_LQI = 0x46
        GET_LAST_FREQUENCY_ESTIMATE = 0x47
        GET_RADIO_ON_TIME = 0x49
        GET_ANNOUNCE_COUNT = 0x4A
        GET_PAGE_FLIPS_COUNT = 0x4B
        GET_SET_TEMPORARY_SLEEP_DWELL = 0x4C
        GET_SECONDS_UNTIL_ANNOUNCE = 0x4D
        GET_SET_AWAKE_DWELL_MILLI_SECONDS = 0x4E
        GET_HW_VERSION = 0x50
        GET_FW_VERSION = 0x51
        GET_BATTERY_LEVEL = 0x52
        GET_DISPLAY_SIZE = 0x53
        GET_MAX_IMAGES = 0x54
        GET_TEMPERATURE = 0x55
        GET_RESET_COUNT = 0x57
        ENABLE_DISABLE_FEATURE = 0x58
        GET_X_RESOLUTION = 0x59
        GET_Y_RESOLUTION = 0x5A
        GET_SET_SCREEN_ORIENTATION = 0x5B
        GET_RASTER_DIRECTIONS = 0x5C
        GET_MAX_TEMPLATES_ALLOWED = 0x5D
        GET_MAX_TEMPLATE_DATA_ALLOWED = 0x5E
        SOFTWARE_RESET = 0x5F

        DISPLAY_UPDATE = 0x77

        DELETE_TEMPLATES = 0x80
        DELETE_TEMPLATE_DATA = 0x81
        GET_TEMPLATE_LIST = 0x82
        GET_TEMPLATE_CRC = 0x83
        GET_TEMPLATE_LIST_COUNT = 0x84
        GET_TEMPLATE_DATA_LIST = 0x85
        GET_TEMPLATE_DATA_CRC = 0x86
        GET_TEMPLATE_DATA_LIST_COUNT = 0x87

        GET_SET_GPIO_OUT_STATE = 0x88
        GET_GPIO_IN_STATE = 0x89
        GET_SET_ACCELEROMETER_STATE = 0x8A
        KEEP_AWAKE = 0x8B
        KEEP_AWAKE_COPY = 0x8C

        IMAGE_LINE = 0xA0
        IMAGE_BLOCK = 0xA1
        IMAGE_ASCII = 0xA2

        GET_FONT_ID_AND_CRC = 0xA4
        FONT_DELETE = 0xA5
        FONT_WRITE = 0xA6
        FONT_VALIDATE = 0xA7

        IMAGE_TEMPLATE_WRITE = 0xA8
        IMAGE_TEMPLATE_DATA = 0xA9

        PAGE_MEMORY_WRITE = 0xAA
        FLASH_MEMORY_WRITE = 0xAB
        FLASH_MEMORY_READ = 0xAC
        TRANSACTION_ID = 0xAD
        GET_SET_IMAGE_INVERT = 0xAF

        FIRMWARE_DATA = 0xB0
        FIRMWARE_CRC = 0xB1
        FIRMWARE_ERASE = 0xB2
        BATTERY_REPLACED = 0xBF
        # SET_HOST_IP_ADDR = 0xD0

        READ_EXT_FLASH = 0xD4
        WRITE_EXT_FLASH = 0xD5

        MULTI_DROP_CMND = 0xD6
        MULTI_DROP_READ = 0xD7
        MULTI_DROP_WRITE = 0xD8

        OMNI_STDOUT = 0xFE

    def windowsRam(self):
        """
        Uses Windows API to check RAM
        """
        kernel32 = ctypes.windll.kernel32
        c_ulong = ctypes.c_ulong

        class MEMORYSTATUS(ctypes.Structure):
            _fields_ = [
                ("dwLength", c_ulong),
                ("dwMemoryLoad", c_ulong),
                ("dwTotalPhys", c_ulong),
                ("dwAvailPhys", c_ulong),
                ("dwTotalPageFile", c_ulong),
                ("dwAvailPageFile", c_ulong),
                ("dwTotalVirtual", c_ulong),
                ("dwAvailVirtual", c_ulong)
            ]

        memoryStatus = MEMORYSTATUS()
        memoryStatus.dwLength = ctypes.sizeof(MEMORYSTATUS)
        kernel32.GlobalMemoryStatus(ctypes.byref(memoryStatus))

    def __init__(self):
        pass
    def OnProcessRawHexData(self, hexstring=None, linenum=None):
        rawdata = bytes.fromhex(hexstring)
        print(bytes.fromhex(hexstring))
        pass
    def __str__(self):
        retval = str(self.tagtype)
        if retval[12:16] == 'VIEW':
            retval = retval[12:17]
        return retval

# (?P<time>[0-9]{4}-[0-9]{2}-[0-9]{2}\s[0-9]{2}:[0-9]{2}:[0-9]{2}).*(?P<uuid>[A-F0-9]{16})\sNewHome\s(?P<newgateway>[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}).*new\:\s\((?P<prevgateway>[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}):[0-1],(?P<newrssi>-?[0-9]+\.[0-9]+)
class ReportTagGatewayAffiliation():
    def __init__(self, rssithreshold=0):
        self.rssithreshold=float(rssithreshold)
        # 2021-06-02 07:48:19.4365|DEBUG|Panasonic.Hdk.Gateway.Internal.Location.Zonal.TagInfo|185|Tag D9AE1500000023AB NewHome 10.16.220.218:0 Reason: previous: (10.16.220.217:0,-69.61,:48:17.4132), new: (10.16.220.218:0,-68.14,:48:17.4132)|
        # 2021-06-02 07:48:14.4324|DEBUG|Panasonic.Hdk.Gateway.Internal.Location.Zonal.TagInfo|121|Tag D9AE1600000027BF NewHome 10.16.220.210:1 Reason: previous: (10.16.220.217:0,-58.78,:48:11.3591), new: (10.16.220.210:1,-55.91,:48:11.3591)|# (?P<uuid>[A-F0-9]{16}).*\((?P<gtwy>[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3})\).*\[(?P<cid>CID[0-9]{1,7})\].*XmitAttmpt0
        # tagaffiliationregex = r'(?P<time>[0-9]{4}-[0-9]{2}-[0-9]{2}\s[0-9]{2}:[0-9]{2}:[0-9]{2}).*(?P<uuid>[A-F0-9]{16})\sNewHome\s(?P<newgateway>[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\:[0-1]{1}).*new\:\s\((?P<prevgateway>[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\:[0-1]{1})\,(?P<newrssi>-?[0-9]+\.[0-9]+)'
        tagaffiliationregex = r'(?P<time>[0-9]{4}-[0-9]{2}-[0-9]{2}\s[0-9]{2}:[0-9]{2}:[0-9]{2}).*(?P<uuid>[A-F0-9]{16})\sNewHome\s(?P<newgateway>[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\:[0-1]{1}).*((Reason\:\s\()|(Reason\: previous:\s\())(?P<prevgateway>(no previous vector)|([0-9]{1,3}.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\:[0-1]{1})).*new.*\,(?P<newrssi>[\-]?[0-9\.]+)'
        self.tagaffiliationregexCompiled = re.compile(tagaffiliationregex)
        self.tagaffiliationdict = SortedDict()

    def Log(self, line, linenum=None):
        grps = self.tagaffiliationregexCompiled.match(str(line, 'UTF-8'))
        if grps:
            newrssi = grps.group('newrssi')
            if float(newrssi) > self.rssithreshold:
                return
            time = grps.group('time')
            uuid = grps.group('uuid')
            newgateway = grps.group('newgateway')
            prevgateway = grps.group('prevgateway')
            self.update(time=time, uuid=uuid, newgateway=newgateway, prevgateway=prevgateway, newrssi=newrssi, linenum=linenum)

    def update(self, time=None, uuid = None, newgateway = None, prevgateway = None, newrssi = None, linenum=None):
        if uuid in self.tagaffiliationdict:
            if newgateway not in self.tagaffiliationdict[uuid].keys():
                self.tagaffiliationdict[uuid][newgateway] = {
                    'uuid':uuid,
                    'time':time,
                    'newgateway':newgateway,
                    'prevgateway':prevgateway,
                    'newrssi':newrssi,
                    'linenum':linenum
                }
            if prevgateway not in self.tagaffiliationdict[uuid].keys():
                self.tagaffiliationdict[uuid][prevgateway] = {
                    'uuid':uuid,
                    'time':time,
                    'newgateway':newgateway,
                    'prevgateway':prevgateway,
                    'newrssi':newrssi,
                    'linenum':linenum
                }
        else:
            self.tagaffiliationdict[uuid] = SortedDict()
            self.tagaffiliationdict[uuid][newgateway] = {
                    'uuid':uuid,
                    'time':time,
                    'newgateway': newgateway,
                    'prevgateway':prevgateway,
                    'newrssi':newrssi,
                    'linenum':linenum
            }
            self.tagaffiliationdict[uuid][prevgateway] = {
                    'uuid':uuid,
                    'time':time,
                    'newgateway': newgateway,
                    'prevgateway':prevgateway,
                    'newrssi':newrssi,
                    'linenum':linenum
            }
    def Report(self, filteronly=None):
        print("Gateway Affiliation: ########################################################")
        if filteronly != None:
            for uuid, affiliationlist in self.tagaffiliationdict.items():
                if filteronly:  # true only if list has length
                    if uuid not in filteronly: continue
                    print(f"{uuid}({TagUID(uuid).HWVersion})")
                    for newgateway, entry in affiliationlist.items():
                        rssi = float(entry['newrssi'])
                        if rssi <= self.rssithreshold:
                            print(f" {newgateway}:{entry}{'' if rssi > self.rssithreshold else f'<===== RSSI <= {self.rssithreshold}'}")

    def ReportTagsAtGateways(self, listtags=None, filteronly=None):
        gatewayTagAffiliation = SortedDict()

        for uuid, affiliationlist in self.tagaffiliationdict.items():
            # print(f"{uuid}({TagUID(uuid).HWVersion})")
            if filteronly and uuid in filteronly: continue
            for gateway, entry in affiliationlist.items():
                if gateway not in gatewayTagAffiliation:
                    gatewayTagAffiliation[gateway] = {
                        'numgen2':(1 if TagUID(uuid).HWVersion == 'Gen2' else 0),
                        'numgen3':(1 if TagUID(uuid).HWVersion == 'Gen3' else 0),
                        'numunknown':(1 if TagUID(uuid).HWVersion == 'Unknown Tag' else 0),
                        'tags':[uuid]
                    }
                else:
                    if uuid not in gatewayTagAffiliation[gateway]:
                        gatewayTagAffiliation[gateway]['tags'].append(uuid)
                        if TagUID(uuid).HWVersion == 'Gen2':
                            gatewayTagAffiliation[gateway]['numgen2'] += 1
                        elif TagUID(uuid).HWVersion == 'Gen3':
                            gatewayTagAffiliation[gateway]['numgen3'] += 1
                        else:
                            gatewayTagAffiliation[gateway]['numunknown'] += 1
        for gateway, entry in gatewayTagAffiliation.items():
            numtags = len(entry['tags'])
            print(f"{gateway} had affinity for {f'{numtags} tag' if numtags == 1 else f'{numtags} tags'}:")
            print(f"    Number Gen2: {gatewayTagAffiliation[gateway]['numgen2']}")
            print(f"    Number Gen3: {gatewayTagAffiliation[gateway]['numgen3']}")
            print(f"    Number Unkn: {gatewayTagAffiliation[gateway]['numunknown']}")

            if listtags:
                for tag in sorted(entry['tags']):
                    print(f"    {tag}({TagUID(tag).HWVersion})")
            foo = 3

class ReportTagCommunicationUML():
    def __init__(self, tag=None):
        if tag:
            self.logdict = SortedDict()
        else:
            self.log = None
        self.tag = tag
        CMDRegEx = r'(?P<time>[0-9]{4}-[0-9]{2}-[0-9]{2}\s[0-9]{2}:[0-9]{2}:[0-9]{2}).*DoExecute TagCmdContext.*(?P<uuid>[A-F0-9]{16}).*(?P<cmd>LEDControl\(Button\)|Multiple|DisplayUpdate|GPO\([0-9]?\)).*\[(?P<cid>CID[0-9]{1,7})\]'
        self.CMDRegEx = re.compile(CMDRegEx)
    def Log(self, line, linenum=None):
        if self.tag:
            grps = self.CMDRegEx.match(str(line, 'UTF-8'))
            if grps and (self.tag == grps['uuid']):
                cid = grps['cid']
                entry = {
                        'time':grps['time'],
                        'linenum':linenum,
                        'cid':grps['cid'],
                        'uuid':grps['uuid'],
                        'cmd':grps['cmd']
                        }
                if cid in self.logdict.keys():
                    self.logdict[cid].append(entry)
                else:
                    self.logdict[cid]=[entry]
                print(linenum, grps['cmd'], line)
    def ReportUML(self):
        # Logiscend->+xAction: CID1234
        # xAction->0x1234: cmd1
        # xAction->-Logiscend: CID1234
        # Logiscend->+xAction: CID1235
        # xAction->0x1234: cmd1
        # xAction->-Logiscend: CID1235
        if self.tag:
            print(f'title Tag {self.tag} commanding')
            for cid, entries in self.logdict.items():
                print(f"Logiscend->+Transaction: {cid}")
                for entry in entries:
                    print(f"Transaction->{entry['uuid']}: {entry['cmd']:_<19}line#:{entry['linenum']}")
                print(f"Transaction->-Logiscend: {cid}")


if __name__ == "__main__":
    # print(ProductType(0))
    # print(TagUID('D9AE150001312345'))
    # foo = LogTime('2021-05-24 18:36:55')
    # print(foo)
    # bar = LogTime('2021-05-24 11:36:55')
    # print(foo-bar)
    # TagUpdateStats().main(sys.argv)
    TagFlipIntegrityStats().main(sys.argv)
    # foo = GetHwVersionCmd(hwver=-1).cmd
    # print(foo.cmdid, foo.len, foo.hwver)
    # foo = GetHwVersionCmd()
    # newoffset, bar = foo.Parse(1, bytearray([1,2,3,4,5,6]))
    # print(newoffset, bar.cmdid)
    sys.exit(0)

