raw_text = """
zeynep607196
elif70566
ece25051
ayse517258
fatma868612
irem412168
buse441093
derya40308
ceren50974
mehmet302336
emir33516
kerem512115
arda839073
eren121604
can572707
burak136105
mert23933
yusuf351539
ahmet756982
melis209319
merve94234
sude83765
damla88071
selin80229
asli445658
yasemin25948
ozge11998
nisa59913
eylul39188
nazli43088
defne16380
nehir60371
ada375663
ilayda63079
yagmur3585208
kubrs847
rabia286710
seyma902161
tugba192525
hilal13545
pelin40954
burcu99407
gul41777
leyla85530
aylin752622
damla17037
serra14083
melike81767
nergis48532
berfin57033
hazal33559
ipek501276
sevgi373050
dilan437094
cansu147595
gizem59867
selen77316
beste30109
emre93784
elif679842
kerem95097
zeynep329033
mert125007
ece76683
burak778286
derya867220
can3260754
irem20175
arda868017
selin14603
kaan6562598
buse237454
onur14006
esra177405
oguz95164
ceren80860
deniz562041
melis423622
tolga22940
kivanc73488
volkan391332
taylan33019
eray25321
ugur15838
koray39470
ilker40535
tarkan31438
levent47184
cenk42803
yasin843123
samet69247
zeynep723485
mertsl89
kerem592772
eceme849
emre721584
"""

lines = [l.strip() for l in raw_text.strip().splitlines() if l.strip()]
print(f"Total non-empty lines in prompt: {len(lines)}")
seen = {}
duplicates = []
for idx, item in enumerate(lines, 1):
    if item in seen:
        duplicates.append((item, seen[item], idx))
    else:
        seen[item] = idx

print(f"Unique usernames: {len(seen)}")
print(f"Duplicates found: {duplicates}")
