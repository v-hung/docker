# QUICK START GUIDE: SFTPGO FTP SERVER

Configuration is fully containerized. No manual network setup is required.

---

## 1. Account Configuration (Web Admin)

1. **Create Master Admin:**
   * Go to: `http://192.168.10.43:8080`
   * Set your Admin username and password on the first run.

2. **Create FTP User:**
   * Log into the Web Admin (`:8080`) -> Go to **Users** -> Click **Add (`+`)**.
   * Set **Username** and **Password**.
   * Set **Home Directory** to: `/srv/sftpgo/data` *(Crucial to see the `in/` folder)*.
   * Go to **Permissions** tab -> Check `*` (Full access) -> Click **Submit**.

---

## 2. File Access (Where to View Files)

* **Via Web Browser (Web Client):**
  * Go to: `http://192.168.10.43:8080/web/client`
  * Log in with your **FTP User** credentials to view/upload files directly in the browser.

* **Via FTP Clients (FileZilla / WinSCP / CMD):**
  * **Host:** `192.168.10.43`
  * **Port:** `21`

* **Via Local Host Server:**
  * All physical files are mapped to the local directory: `./ftp_share/`

---

## 3. Java Logging Note

The Java `ProtocolCommandListener` only captures the **Control Channel (Port 21)** commands (`LIST`, `226 Closing`). Filenames are transferred via the **Data Channel**, so they will not appear in the command listener logs. You must manually iterate through `ftpClient.listFiles()` to print them.