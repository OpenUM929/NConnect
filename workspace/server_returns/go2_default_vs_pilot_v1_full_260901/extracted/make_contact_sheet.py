import sys
from pathlib import Path
import cv2, numpy as np
vp=Path(sys.argv[1]); out=Path(sys.argv[2]); label_prefix=sys.argv[3]
cap=cv2.VideoCapture(str(vp)); count=int(cap.get(cv2.CAP_PROP_FRAME_COUNT)); fps=float(cap.get(cv2.CAP_PROP_FPS) or 0)
if count <= 0: raise SystemExit(f'bad frame count {count}: {vp}')
thumbs=[]
for frac in np.linspace(0.03,0.97,12):
    idx=max(0,min(count-1,int(round(frac*(count-1)))))
    cap.set(cv2.CAP_PROP_POS_FRAMES,idx); ok,frame=cap.read()
    if not ok: continue
    h,w=frame.shape[:2]; frame=cv2.resize(frame,(320,max(1,int(h*320/w))),interpolation=cv2.INTER_AREA)
    label=f'{label_prefix} | {idx/fps:.1f}s' if fps else f'{label_prefix} | frame {idx}'
    cv2.rectangle(frame,(0,0),(frame.shape[1],28),(0,0,0),-1); cv2.putText(frame,label,(5,19),cv2.FONT_HERSHEY_SIMPLEX,0.38,(255,255,255),1,cv2.LINE_AA); thumbs.append(frame)
cap.release()
if not thumbs: raise SystemExit(f'no readable frames: {vp}')
th=max(x.shape[0] for x in thumbs); normalized=[cv2.copyMakeBorder(x,0,th-x.shape[0],0,0,cv2.BORDER_CONSTANT,value=(30,30,30)) if x.shape[0]<th else x for x in thumbs]
rows=[cv2.hconcat(normalized[i:i+4]) for i in range(0,len(normalized),4)]; sheet=cv2.vconcat(rows); out.parent.mkdir(parents=True,exist_ok=True)
if not cv2.imwrite(str(out),sheet,[int(cv2.IMWRITE_JPEG_QUALITY),92]): raise SystemExit(f'write failed: {out}')
print(f'{vp.name}\tframes={count}\tfps={fps}\tduration={count/fps if fps else 0:.3f}\t{out.name}')
