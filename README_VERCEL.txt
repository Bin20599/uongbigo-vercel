UONG BI GO - BAN VERCEL + SUPABASE

1) Tao database Supabase
- Vao https://supabase.com/ va tao project moi.
- Mo SQL Editor > New query.
- Mo file supabase.sql trong project nay, copy toan bo vao SQL Editor va Run.

2) Lay thong tin database
- Supabase > Project Settings > API.
- Copy Project URL.
- Copy Service Role Key (giu bi mat, khong dua vao JavaScript/frontend).

3) Dua code len GitHub
- Tao repository moi tren GitHub, vi du: uongbigo-vercel.
- Upload TOAN BO file/folder cua project nay vao repository.

4) Deploy Vercel
- Vao https://vercel.com/ > Add New > Project > Import Git Repository.
- Chon repo uongbigo-vercel > Deploy.
- Neu Vercel hoi Framework, chon Other/None; khong can Build Command cho bo HTML nay.

5) Them Environment Variables tren Vercel
Vercel > Project > Settings > Environment Variables:
SUPABASE_URL = URL cua Supabase
SUPABASE_SERVICE_ROLE_KEY = Service Role Key cua Supabase
VERCEL_AUTH_SECRET = mot chuoi bi mat dai, vi du: UBG-2026-DO-NOT-SHARE-9f31a2
Sau do Redeploy.

6) Test
- Mo link .vercel.app.
- Tai khoan admin: admin@uongbigo.vn / Admin@123
- Tai khoan bep: bep@uongbigo.vn / Bep@123
- Tai khoan sinh vien: sv@uongbigo.vn / sv@123

Luu y:
- Day la ban demo hoc tap. Service Role Key chi duoc dat trong Vercel Environment Variables, tuyet doi khong viet vao JS.
- Chuc nang QR hien tai van la QR gia lap nhu ban XAMPP, chua ket noi ngan hang/thanh toan that.
- Khi GitHub push code moi, Vercel co the tu dong deploy lai neu repo da duoc ket noi.
