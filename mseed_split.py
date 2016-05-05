import obspy
infile = "c:\\caldata\\KUR\\S0116125\\61250400.SZ1"
st=obspy.read(infile)
start = st[0].stats.starttime
fout = "C:\\caldata\\KUR\\S0116125\\612504_"
for i in range(0,50):
    sp = st.slice(start+i*60,start+(i+1)*60)
    f = fout+str(i)+".SZ1"
    sp.write(f,format="mseed")