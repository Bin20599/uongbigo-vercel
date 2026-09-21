import os, json, base64, hashlib, hmac, secrets, urllib.request, urllib.parse
from datetime import datetime, timezone, timedelta

SUPABASE_URL = os.environ.get('SUPABASE_URL', '').rstrip('/')
SUPABASE_KEY = os.environ.get('SUPABASE_SERVICE_ROLE_KEY', '')
AUTH_SECRET = os.environ.get('VERCEL_AUTH_SECRET', 'change-me-in-vercel')


def response(body, status=200):
    return {
        'statusCode': status,
        'headers': {'Content-Type': 'application/json; charset=utf-8', 'Access-Control-Allow-Origin': '*', 'Access-Control-Allow-Headers': 'Content-Type, X-UBG-Token', 'Access-Control-Allow-Methods': 'GET,POST,PUT,PATCH,DELETE,OPTIONS'},
        'body': json.dumps(body, ensure_ascii=False, default=str)
    }


def supabase(method, table, query='', body=None):
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise RuntimeError('Chua cau hinh SUPABASE_URL va SUPABASE_SERVICE_ROLE_KEY tren Vercel.')
    url = f'{SUPABASE_URL}/rest/v1/{table}' + (('?' + query) if query else '')
    headers = {'apikey': SUPABASE_KEY, 'Authorization': 'Bearer ' + SUPABASE_KEY, 'Content-Type': 'application/json', 'Prefer': 'return=representation'}
    data = None if body is None else json.dumps(body, ensure_ascii=False).encode()
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            raw = r.read().decode('utf-8')
            return json.loads(raw) if raw else []
    except urllib.error.HTTPError as e:
        msg = e.read().decode('utf-8', errors='replace')
        raise RuntimeError(msg)


def sha256(s):
    return hashlib.sha256(s.encode()).hexdigest()


def make_token(user):
    payload = {'id': int(user['maNguoiDung']), 'email': user['email'], 'role': user['vaiTro'], 'exp': int(datetime.now(timezone.utc).timestamp()) + 86400 * 7}
    raw = base64.urlsafe_b64encode(json.dumps(payload, separators=(',', ':')).encode()).decode().rstrip('=')
    sig = hmac.new(AUTH_SECRET.encode(), raw.encode(), hashlib.sha256).hexdigest()
    return raw + '.' + sig


def current_user(req):
    token = (req.get('headers') or {}).get('x-ubg-token') or (req.get('headers') or {}).get('X-UBG-Token')
    if not token or '.' not in token:
        return None
    raw, sig = token.rsplit('.', 1)
    good = hmac.new(AUTH_SECRET.encode(), raw.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(sig, good): return None
    try:
        payload = json.loads(base64.urlsafe_b64decode(raw + '=' * (-len(raw) % 4)))
        if payload.get('exp', 0) < int(datetime.now(timezone.utc).timestamp()): return None
        rows = supabase('GET', 'users', 'maNguoiDung=eq.' + str(int(payload['id'])) + '&select=maNguoiDung,hoTen,email,vaiTro')
        return rows[0] if rows else None
    except Exception:
        return None


def require_user(req):
    u = current_user(req)
    if not u: raise ApiError(401, 'Phien dang nhap da het han, vui long dang nhap lai.')
    return u


class ApiError(Exception):
    def __init__(self, status, message): self.status, self.message = status, message


def menu_view(r):
    return {'maMon': int(r['maMon']), 'tenMon': r['tenMon'], 'donGia': float(r['donGia']), 'moTa': r.get('moTa') or '', 'hinhAnh': r.get('hinhAnh') or '', 'trangThai': r['trangThai']}


def order_view(o):
    items = supabase('GET', 'order_items', 'maDonHang=eq.' + str(o['maDonHang']) + '&select=maMon,tenMon,soLuong,donGia&order=id.asc')
    return {'maDonHang': int(o['maDonHang']), 'maDonRutGon': o['maDonRutGon'], 'ngayDat': o['ngayDat'], 'thoiGianNhan': o.get('thoiGianNhan'), 'trangThai': o['trangThai'], 'tongTien': float(o['tongTien']), 'chiTietDonHangs': [{'maMon': int(x['maMon']), 'tenMon': x['tenMon'], 'soLuong': int(x['soLuong']), 'donGia': float(x['donGia'])} for x in items]}


def body(req):
    b = req.get('body')
    if isinstance(b, str):
        try: return json.loads(b) if b else {}
        except Exception: return {}
    return b or {}


def handler(req):
    if req.get('method') == 'OPTIONS': return response({}, 200)
    method = req.get('method', 'GET').upper()
    q = req.get('query') or {}
    path = q.get('path', '/')
    if isinstance(path, list): path = path[0]
    path = '/' + str(path).strip('/')
    b = body(req)
    try:
        # AUTH
        if method == 'POST' and path == '/auth/login':
            email = str(b.get('email', '')).strip().lower(); pw = str(b.get('matKhau', ''))
            rows = supabase('GET', 'users', 'email=eq.' + urllib.parse.quote(email, safe='') + '&select=*&limit=1')
            if not rows or not hmac.compare_digest(rows[0]['matKhau'], sha256(pw)): raise ApiError(401, 'Sai email hoac mat khau.')
            u = rows[0]; uv = {'maNguoiDung': int(u['maNguoiDung']), 'hoTen': u['hoTen'], 'email': u['email'], 'vaiTro': u['vaiTro']}
            redirect = {'ROLE_BUYER':'menu.html','ROLE_STAFF':'kds.html','ROLE_ADMIN':'admin/dashboard.html'}.get(u['vaiTro'], 'index.html')
            return response({'accessToken': make_token(u), 'nguoiDung': uv, 'redirectTo': redirect})

        if method == 'POST' and path == '/auth/register':
            email = str(b.get('email', '')).strip().lower(); name = str(b.get('hoTen', '')).strip(); pw = str(b.get('matKhau', ''))
            role = b.get('vaiTro') if b.get('vaiTro') in ('ROLE_BUYER','ROLE_STAFF') else 'ROLE_BUYER'
            if not name or not email or len(pw) < 6: raise ApiError(400, 'Vui long nhap day du thong tin hop le.')
            if supabase('GET', 'users', 'email=eq.' + urllib.parse.quote(email, safe='') + '&select=maNguoiDung'):
                raise ApiError(409, 'Email nay da duoc su dung.')
            supabase('POST', 'users', body={'hoTen':name,'email':email,'matKhau':sha256(pw),'vaiTro':role})
            return response({'message':'Dang ky thanh cong.'})

        if method == 'POST' and path == '/auth/forgot-password':
            email = str(b.get('email', '')).strip().lower(); rows = supabase('GET','users','email=eq.'+urllib.parse.quote(email,safe='')+'&select=maNguoiDung')
            if not rows: raise ApiError(404, 'Khong tim thay tai khoan voi email nay.')
            tmp = 'Tam@' + str(secrets.randbelow(9000)+1000)
            supabase('PATCH','users','maNguoiDung=eq.'+str(rows[0]['maNguoiDung']), {'matKhau':sha256(tmp)})
            return response({'message':'Da tao mat khau tam thoi, ban co the dang nhap ngay bang mat khau nay.','matKhauTamThoi':tmp})

        # MENU
        if method == 'GET' and path == '/menu':
            rows = supabase('GET','menu_items','trangThai=neq.DA_XOA&select=*&order=maMon.asc')
            return response([menu_view(x) for x in rows])

        # ORDERS
        if method == 'GET' and path == '/donhang/cua-toi':
            u = require_user(req); rows = supabase('GET','orders','maNguoiDung=eq.'+str(u['maNguoiDung'])+'&select=*&order=ngayDat.desc')
            return response([order_view(x) for x in rows])

        if method == 'POST' and path == '/donhang':
            u = require_user(req); items = b.get('items') if isinstance(b.get('items'), list) else []
            if not items: raise ApiError(400,'Gio hang dang trong.')
            details=[]; total=0
            for it in items:
                mid=int(it.get('maMon',0)); qty=max(1,int(it.get('soLuong',1)))
                rows=supabase('GET','menu_items','maMon=eq.'+str(mid)+'&trangThai=eq.CON_HANG&select=*&limit=1')
                if not rows: continue
                m=rows[0]; d={'maMon':int(m['maMon']),'tenMon':m['tenMon'],'soLuong':qty,'donGia':float(m['donGia'])}; details.append(d); total += d['donGia']*qty
            if not details: raise ApiError(400,'Cac mon trong gio hang hien khong con hang.')
            now=datetime.now(timezone.utc).isoformat(); short='DH'+str(int(datetime.now().timestamp()*1000))[-6:]
            created=supabase('POST','orders',body={'maNguoiDung':u['maNguoiDung'],'maDonRutGon':short,'ngayDat':now,'thoiGianNhan':b.get('thoiGianNhan') or now,'trangThai':'CHO_THANH_TOAN','tongTien':total})[0]
            oid=int(created['maDonHang']); supabase('PATCH','orders','maDonHang=eq.'+str(oid),{'maDonRutGon':'DH'+str(oid).zfill(4)})
            for d in details: supabase('POST','order_items',body={'maDonHang':oid,**d})
            created=supabase('GET','orders','maDonHang=eq.'+str(oid)+'&select=*')[0]
            return response(order_view(created))

        # PAYMENT
        if method == 'POST' and path.startswith('/thanhtoan/') and path.endswith('/qr'):
            require_user(req); oid=int(path.split('/')[2]); rows=supabase('GET','orders','maDonHang=eq.'+str(oid)+'&select=*')
            if not rows: raise ApiError(404,'Khong tim thay don hang.')
            o=rows[0]
            if o['trangThai']!='CHO_THANH_TOAN': raise ApiError(400,'Don hang nay khong o trang thai cho thanh toan.')
            qr='QR'+str(oid)+'-'+str(int(datetime.now().timestamp())); exp=(datetime.now(timezone.utc)+timedelta(minutes=5)).isoformat()
            supabase('PATCH','orders','maDonHang=eq.'+str(oid),{'maQr':qr,'thoiHanThanhToan':exp})
            return response({'maDonHang':oid,'maQr':qr,'phuongThuc':q.get('phuongThuc','VIETQR'),'soTien':float(o['tongTien']),'qrImageBase64':None,'thoiHanThanhToan':exp})

        if method == 'POST' and path == '/thanhtoan/webhook':
            require_user(req); oid=int(b.get('maDonHang',0)); qr=str(b.get('maQr','')); rows=supabase('GET','orders','maDonHang=eq.'+str(oid)+'&maQr=eq.'+urllib.parse.quote(qr,safe='')+'&select=*')
            if not rows: raise ApiError(404,'Khong tim thay giao dich thanh toan.')
            status='DA_THANH_TOAN' if b.get('ketQua')=='THANH_CONG' else 'CHO_THANH_TOAN'; supabase('PATCH','orders','maDonHang=eq.'+str(oid),{'trangThai':status})
            return response(order_view(supabase('GET','orders','maDonHang=eq.'+str(oid)+'&select=*')[0]))

        # KDS
        if method == 'GET' and path == '/kds/orders':
            require_user(req); rows=supabase('GET','orders','trangThai=in.(DA_THANH_TOAN,DANG_CHUAN_BI,SAN_SANG_NHAN)&select=*&order=ngayDat.asc')
            return response([order_view(x) for x in rows])
        if method == 'PATCH' and path.startswith('/kds/orders/') and path.endswith('/status'):
            require_user(req); oid=int(path.split('/')[3]); rows=supabase('GET','orders','maDonHang=eq.'+str(oid)+'&select=*')
            if not rows: raise ApiError(404,'Khong tim thay don hang.')
            supabase('PATCH','orders','maDonHang=eq.'+str(oid),{'trangThai':str(b.get('trangThaiMoi',''))})
            return response(order_view(supabase('GET','orders','maDonHang=eq.'+str(oid)+'&select=*')[0]))
        if method == 'PATCH' and path.startswith('/kds/mon/') and path.endswith('/toggle'):
            require_user(req); mid=int(path.split('/')[3]); rows=supabase('GET','menu_items','maMon=eq.'+str(mid)+'&select=*')
            if not rows: raise ApiError(404,'Khong tim thay mon an.')
            new='HET_HANG' if rows[0]['trangThai']=='CON_HANG' else 'CON_HANG'; supabase('PATCH','menu_items','maMon=eq.'+str(mid),{'trangThai':new})
            return response(menu_view(supabase('GET','menu_items','maMon=eq.'+str(mid)+'&select=*')[0]))

        # ADMIN
        if method == 'GET' and path == '/admin/thong-ke':
            require_user(req); rows=supabase('GET','orders','select=tongTien,trangThai')
            paid={'DA_THANH_TOAN','DANG_CHUAN_BI','SAN_SANG_NHAN','HOAN_THANH'}; total=sum(float(x['tongTien']) for x in rows if x['trangThai'] in paid); done=sum(1 for x in rows if x['trangThai']=='HOAN_THANH')
            menu=supabase('GET','menu_items','select=trangThai'); selling=sum(1 for x in menu if x['trangThai']=='CON_HANG'); outstock=sum(1 for x in menu if x['trangThai']=='HET_HANG')
            return response({'tongDoanhThu':total,'tongSoDonHoanThanh':done,'tongSoDonTatCa':len(rows),'soMonDangBan':selling,'soMonHetHang':outstock})
        if method == 'GET' and path == '/admin/don-hang':
            require_user(req); rows=supabase('GET','orders','select=*&order=ngayDat.desc'); return response([order_view(x) for x in rows])
        if method == 'GET' and path == '/admin/mon-an':
            require_user(req); rows=supabase('GET','menu_items','select=*&order=maMon.asc'); return response([menu_view(x) for x in rows])
        if method == 'POST' and path == '/admin/mon-an':
            require_user(req); name=str(b.get('tenMon','')).strip(); price=float(b.get('donGia',0) or 0)
            if not name or price<=0: raise ApiError(400,'Ten mon va don gia khong hop le.')
            r=supabase('POST','menu_items',body={'tenMon':name,'donGia':price,'moTa':b.get('moTa',''),'hinhAnh':b.get('hinhAnh',''),'trangThai':'CON_HANG'})[0]; return response(menu_view(r))
        if method == 'PUT' and path.startswith('/admin/mon-an/'):
            require_user(req); mid=int(path.split('/')[-1]); name=str(b.get('tenMon','')).strip(); price=float(b.get('donGia',0) or 0)
            if not name or price<=0: raise ApiError(400,'Ten mon va don gia khong hop le.')
            patch={'tenMon':name,'donGia':price,'moTa':b.get('moTa',''),'hinhAnh':b.get('hinhAnh','')}
            if b.get('trangThai') is not None: patch['trangThai']=b['trangThai']
            r=supabase('PATCH','menu_items','maMon=eq.'+str(mid),patch)
            if not r: raise ApiError(404,'Khong tim thay mon an.')
            return response(menu_view(r[0]))
        if method == 'DELETE' and path.startswith('/admin/mon-an/'):
            require_user(req); mid=int(path.split('/')[-1]); supabase('PATCH','menu_items','maMon=eq.'+str(mid),{'trangThai':'DA_XOA'}); return response({'message':'Da xoa mon an.'})
        raise ApiError(404,'Khong tim thay endpoint.')
    except ApiError as e:
        return response({'message':e.message}, e.status)
    except Exception as e:
        return response({'message':'Loi may chu: '+str(e)}, 500)

# Vercel Python runtime accepts a function named handler.
def main(request):
    return handler(request)
