import requests
import time
import json
from datetime import datetime
import threading
import sys
import select
import msvcrt
import os
import random
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.layout import Layout
from rich.panel import Panel
from rich.text import Text
from rich.align import Align
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.columns import Columns
from rich.rule import Rule
from rich.padding import Padding
from rich.box import ROUNDED, DOUBLE, MINIMAL
from rich import print as rprint
from rich.spinner import Spinner

class CryptoTrackerGenZ:
    def __init__(self):
        self.console = Console()
        self.running = True
        self.watchlist = [
            'bitcoin', 'ethereum', 'binancecoin', 'cardano', 'solana', 
            'polkadot', 'dogecoin', 'avalanche-2', 'chainlink', 'polygon'
        ]
        self.crypto_data = {}
        self.update_interval = 15  
        self.loading = False
        self.animation_frame = 0
        self.price_history = {}  
        self.last_prices = {}
        
        self.crypto_icons = {
            'bitcoin': 'BTC',
            'ethereum': 'ETH',
            'binancecoin': 'BNB',
            'cardano': 'ADA',
            'solana': 'SOL',
            'polkadot': 'DOT',
            'dogecoin': 'DOGE',
            'avalanche-2': 'AVAX',
            'chainlink': 'LINK',
            'polygon': 'MATIC'
        }
        
        self.wave_chars = ['▁', '▂', '▃', '▄', '▅', '▆', '▇', '█']
        self.loading_chars = ['⣾', '⣽', '⣻', '⢿', '⡿', '⣟', '⣯', '⣷']
        
    def get_trend_animation(self, coin_id):
        """Bikin grafik mini yang smooth"""
        if coin_id not in self.price_history:
            return "━━━"
        
        history = self.price_history[coin_id]
        if len(history) < 2:
            return "━━━"

        if len(history) >= 5:
            recent = history[-5:]
            min_val = min(recent)
            max_val = max(recent)
            if max_val == min_val:
                return "━━━━━"
            
            sparkline = ""
            for val in recent:
                normalized = (val - min_val) / (max_val - min_val)
                char_idx = int(normalized * (len(self.wave_chars) - 1))
                sparkline += self.wave_chars[char_idx]
            return sparkline
        
        return "━━━"

    def get_price_change_indicator(self, coin_id, current_price):
        """Indikator perubahan harga yang clean"""
        if coin_id in self.last_prices:
            last_price = self.last_prices[coin_id]
            if current_price > last_price:
                return "[bright_green]▲[/bright_green]"
            elif current_price < last_price:
                return "[bright_red]▼[/bright_red]"
            else:
                return "[yellow]●[/yellow]"
        return "[dim]○[/dim]"

    def fetch_crypto_data(self):
        """Ambil data crypto dari API dengan handling yang proper"""
        self.loading = True
        try:
            coins = ','.join(self.watchlist)
            url = f"https://api.coingecko.com/api/v3/simple/price"
            params = {
                'ids': coins,
                'vs_currencies': 'usd',
                'include_24hr_change': 'true',
                'include_24hr_vol': 'true',
                'include_market_cap': 'true'
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            for coin_id in self.crypto_data:
                self.last_prices[coin_id] = self.crypto_data[coin_id].get('price', 0)

            for coin_id, info in data.items():
                price = info.get('usd', 0)

                if coin_id not in self.price_history:
                    self.price_history[coin_id] = []
                self.price_history[coin_id].append(price)
                if len(self.price_history[coin_id]) > 20:  
                    self.price_history[coin_id].pop(0)
                
                self.crypto_data[coin_id] = {
                    'name': coin_id.replace('-', ' ').title().replace('2', ''),
                    'price': price,
                    'change_24h': info.get('usd_24h_change', 0),
                    'volume_24h': info.get('usd_24h_vol', 0),
                    'market_cap': info.get('usd_market_cap', 0),
                    'icon': self.crypto_icons.get(coin_id, 'COIN')
                }
                
        except requests.exceptions.RequestException as e:
            self.console.print(f"[red]Koneksi bermasalah nih: {e}[/red]")
        except Exception as e:
            self.console.print(f"[red]Ada error: {e}[/red]")
        finally:
            self.loading = False

    def format_number(self, num):
        """Format angka besar jadi lebih readable"""
        if num >= 1e12:
            return f"[bright_blue]{num/1e12:.2f}T[/bright_blue]"
        elif num >= 1e9:
            return f"[bright_cyan]{num/1e9:.2f}B[/bright_cyan]"
        elif num >= 1e6:
            return f"[bright_magenta]{num/1e6:.2f}M[/bright_magenta]"
        elif num >= 1e3:
            return f"[bright_yellow]{num/1e3:.2f}K[/bright_yellow]"
        else:
            return f"[white]{num:.2f}[/white]"

    def create_animated_header(self):
        """Headers"""
        current_time = datetime.now().strftime("%H:%M:%S")

        spinner_char = self.loading_chars[self.animation_frame % len(self.loading_chars)]

        title_text = Text()
        title_text.append("CRYPTO ", style="bold bright_green")
        title_text.append("TRACKER", style="bold bright_blue")
        title_text.append(" v2.0", style="dim bright_white")

        status_line = Text()
        if self.loading:
            status_line.append(f"{spinner_char} ", style="bright_green")
            status_line.append("Lagi ngambil data...", style="bright_green")
        else:
            status_line.append("● ", style="bright_green")
            status_line.append("LIVE", style="bold bright_green")
        
        status_line.append(f" | {current_time} | ", style="dim white")
        status_line.append(f"{len(self.watchlist)} koin ditrack", style="bright_cyan")
        
        header_content = Align.center(
            Text.assemble(title_text, "\n", status_line)
        )
        
        return Panel(
            header_content,
            title="[bold bright_magenta]DASHBOARD MARKET[/bold bright_magenta]",
            border_style="bright_magenta",
            box=DOUBLE
        )

    def create_crypto_table(self):
        """Table crypto yang clean dan informatif"""
        table = Table(
            title="[bold bright_cyan]DATA MARKET REAL-TIME[/bold bright_cyan]",
            title_style="bold",
            box=ROUNDED,
            header_style="bold bright_white on blue",
            show_lines=True
        )
        
        table.add_column("KOIN", style="bright_cyan", no_wrap=True, width=12)
        table.add_column("HARGA", justify="right", style="bright_green", width=15)
        table.add_column("TREND", justify="center", width=8)
        table.add_column("24H", justify="right", width=12)
        table.add_column("VOLUME", justify="right", style="bright_blue", width=12)
        table.add_column("MARKET CAP", justify="right", style="bright_yellow", width=12)

        sorted_coins = sorted(
            self.crypto_data.items(),
            key=lambda x: x[1].get('market_cap', 0),
            reverse=True
        )
        
        for i, (coin_id, data) in enumerate(sorted_coins):

            rank_indicators = ["#1", "#2", "#3"] + [f"#{i+1}" for i in range(3, 10)]
            rank = rank_indicators[i] if i < len(rank_indicators) else f"#{i+1}"
        
            price = data['price']
            change_indicator = self.get_price_change_indicator(coin_id, price)
            
            if price < 1:
                price_text = f"${price:.6f}"
            else:
                price_text = f"${price:,.2f}"
            
            change = data['change_24h']
            if change > 5:
                change_style = "bold bright_green"
                change_icon = "PUMP"
            elif change > 0:
                change_style = "bright_green"
                change_icon = "UP"
            elif change > -5:
                change_style = "bright_red"
                change_icon = "DOWN"
            else:
                change_style = "bold bright_red"
                change_icon = "DUMP"
            
            change_text = f"[{change_style}]{change_icon} {change:+.2f}%[/{change_style}]"
            trend = self.get_trend_animation(coin_id)
            
            table.add_row(
                f"{rank} {data['icon']}",
                f"{price_text} {change_indicator}",
                f"[dim]{trend}[/dim]",
                change_text,
                self.format_number(data['volume_24h']),
                self.format_number(data['market_cap'])
            )
        
        return table

    def create_progress_panel(self):
        """Panel progress yang smooth"""
        elapsed = time.time() % self.update_interval
        progress_percent = (elapsed / self.update_interval) * 100

        bar_length = 30
        filled_length = int(bar_length * progress_percent // 100)
        bar = '█' * filled_length + '░' * (bar_length - filled_length)
        
        progress_text = Text()
        progress_text.append("Next Update: ", style="bright_white")
        progress_text.append(f"[bright_green]{bar}[/bright_green] ")
        progress_text.append(f"{progress_percent:.0f}%", style="bright_yellow")

        total_volume = sum(data.get('volume_24h', 0) for data in self.crypto_data.values())
        avg_change = sum(data.get('change_24h', 0) for data in self.crypto_data.values()) / len(self.crypto_data) if self.crypto_data else 0
        
        market_status = Text()
        if avg_change > 2:
            market_status.append("MARKET BULLISH", style="bold bright_green")
        elif avg_change < -2:
            market_status.append("MARKET BEARISH", style="bold bright_red")
        else:
            market_status.append("MARKET SIDEWAYS", style="bright_yellow")
        
        market_status.append(f" | Total Volume: {self.format_number(total_volume)}", style="dim white")
        
        content = Text.assemble(progress_text, "\n", market_status)
        
        return Panel(
            Align.center(content),
            title="[bold bright_blue]Status Market & Update[/bold bright_blue]",
            border_style="bright_blue",
            box=MINIMAL
        )

    def create_controls_panel(self):
        """Panel kontrol yang clean"""
        controls = [
            ("KELUAR", "Tekan 'Q'", "bright_red"),
            ("REFRESH", "Tekan 'R'", "bright_green"),
            ("TAMBAH", "Tekan 'A'", "bright_yellow"),
            ("HAPUS", "Tekan 'D'", "bright_magenta")
        ]
        
        controls_columns = []
        for action, key, color in controls:
            control_text = Text()
            control_text.append(f"{action}\n", style=f"bold {color}")
            control_text.append(key, style="dim white")
            controls_columns.append(Panel(Align.center(control_text), border_style=color, box=MINIMAL))
        
        return Panel(
            Columns(controls_columns, equal=True, expand=True),
            title="[bold bright_cyan]KONTROL[/bold bright_cyan]",
            border_style="bright_cyan"
        )

    def create_footer_panel(self):
        """Footer yang minimalis"""
        footer_text = Text()
        footer_text.append("Dibuat oleh: ", style="dim white")
        footer_text.append("M. Imam Iryunullah", style="bold bright_magenta")
        footer_text.append(" | ", style="dim white")
        footer_text.append("Real-time Crypto Tracker", style="bright_cyan")
        footer_text.append(" | ", style="dim white")
        footer_text.append("Dibuat dengan Python", style="dim white")
        
        return Panel(
            Align.center(footer_text),
            border_style="dim white",
            box=MINIMAL
        )

    def create_layout(self):
        """Layout utama yang terorganisir"""
        layout = Layout()
        
        layout.split_column(
            Layout(self.create_animated_header(), size=5, name="header"),
            Layout(self.create_crypto_table(), name="main"),
            Layout(self.create_progress_panel(), size=4, name="progress"),
            Layout(self.create_controls_panel(), size=6, name="controls"),
            Layout(self.create_footer_panel(), size=3, name="footer")
        )
        
        return layout

    def handle_input(self):
        """Handle input keyboard - compatible Windows & Linux"""
        while self.running:
            try:
                if os.name == 'nt': 
                    if msvcrt.kbhit():
                        key = msvcrt.getch().decode('utf-8').lower()
                        if key == 'q':
                            self.running = False
                            break
                        elif key == 'r':
                            self.fetch_crypto_data()
                            time.sleep(0.5)
                        elif key == 'a':
                            self.add_coin_interactive()
                            time.sleep(0.5)
                        elif key == 'd':
                            self.remove_coin_interactive()
                            time.sleep(0.5)
                else: 
                    if select.select([sys.stdin], [], [], 0.1)[0]:
                        key = sys.stdin.read(1).lower()
                        if key == 'q':
                            self.running = False
                            break
                        elif key == 'r':
                            self.fetch_crypto_data()
                        elif key == 'a':
                            self.add_coin_interactive()
                        elif key == 'd':
                            self.remove_coin_interactive()
                
                time.sleep(0.1)
            except:
                break

    def add_coin_interactive(self):
        """Tambah koin baru ke watchlist"""
        with self.console.capture() as capture:
            self.console.print("\n[bold bright_yellow]Tambah Crypto Baru[/bold bright_yellow]")
            self.console.print("[dim]Contoh: ripple, litecoin, uniswap, cosmos, algorand[/dim]")
            
        try:
            self.console.print("[bright_green]Masukkan ID koin: [/bright_green]", end="")
            coin_id = input().lower().strip()
            
            if coin_id and coin_id not in self.watchlist:
                self.watchlist.append(coin_id)
                self.console.print(f"[bold bright_green]Berhasil ditambah: {coin_id}[/bold bright_green]")
                self.fetch_crypto_data()
            else:
                self.console.print("[bright_red]Koin udah ada atau input salah![/bright_red]")
        except:
            pass

    def remove_coin_interactive(self):
        """Hapus koin dari watchlist"""
        if len(self.watchlist) <= 1:
            self.console.print("[bright_red]Ga bisa dihapus - minimal harus ada 1 koin![/bright_red]")
            return
            
        try:
            self.console.print(f"\n[bold bright_yellow]Hapus Cryptocurrency[/bold bright_yellow]")
            self.console.print(f"[bright_cyan]Koin saat ini: {', '.join(self.watchlist)}[/bright_cyan]")
            self.console.print("[bright_green]ID koin yang mau dihapus: [/bright_green]", end="")
            coin_id = input().lower().strip()
            
            if coin_id in self.watchlist:
                self.watchlist.remove(coin_id)
                if coin_id in self.crypto_data:
                    del self.crypto_data[coin_id]
                if coin_id in self.price_history:
                    del self.price_history[coin_id]
                self.console.print(f"[bold bright_green]Berhasil dihapus: {coin_id}[/bold bright_green]")
            else:
                self.console.print("[bright_red]Koin ga ditemukan di watchlist![/bright_red]")
        except:
            pass

    def run(self):
        """Main loop dengan startup yang smooth"""
        self.console.clear()
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TimeElapsedColumn(),
            console=self.console
        ) as progress:
            startup_task = progress.add_task("[bright_green]Memulai Crypto Tracker...", total=100)
            
            for i in range(100):
                if i < 30:
                    progress.update(startup_task, description="[bright_blue]Loading modules...", advance=1)
                elif i < 60:
                    progress.update(startup_task, description="[bright_yellow]Koneksi ke API...", advance=1)
                elif i < 90:
                    progress.update(startup_task, description="[bright_green]Ambil data market...", advance=1)
                else:
                    progress.update(startup_task, description="[bright_magenta]Siap diluncurkan!", advance=1)
                time.sleep(0.02)

        self.console.print("[bold bright_green]Loading data market awal...[/bold bright_green]")
        self.fetch_crypto_data()

        input_thread = threading.Thread(target=self.handle_input, daemon=True)
        input_thread.start()
        
        try:
            with Live(self.create_layout(), refresh_per_second=2, screen=True) as live: 
                last_update = time.time()
                
                while self.running:
                    current_time = time.time()

                    self.animation_frame += 1

                    if current_time - last_update >= self.update_interval:
                        self.fetch_crypto_data()
                        last_update = current_time

                    live.update(self.create_layout())
                    time.sleep(0.5)
                    
        except KeyboardInterrupt:
            pass

        self.console.clear()
        self.console.print("\n[bold bright_magenta]Thanks udah pake Crypto Tracker![/bold bright_magenta]")
        self.console.print("[dim]Dibuat oleh M. Imam Iryunullah[/dim]")
        self.console.print("[bold bright_cyan]Keep trading! Stay safe![/bold bright_cyan]\n")

def check_and_install_dependencies():
    """Check dan auto-install dependencies yang dibutuhkan"""
    required_packages = {
        'requests': 'requests',
        'rich': 'rich'
    }
    
    missing_packages = []

    for module_name, package_name in required_packages.items():
        try:
            __import__(module_name)
        except ImportError:
            missing_packages.append(package_name)
    
    if not missing_packages:
        return True

    print("\n" + "="*60)
    print("CRYPTO TRACKER - AUTO INSTALLER")
    print("="*60)
    print(f"Package yang kurang: {', '.join(missing_packages)}")
    print("Mulai install otomatis...\n")
    
    import subprocess
    import sys
    
    for package in missing_packages:
        print(f"Installing {package}...")

        def show_install_animation(package_name):
            animation_chars = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
            import threading
            import time
            
            def animate():
                i = 0
                while getattr(animate, 'running', True):
                    print(f"\r   {animation_chars[i % len(animation_chars)]} Installing {package_name}...", end='', flush=True)
                    i += 1
                    time.sleep(0.1)
            
            animation_thread = threading.Thread(target=animate)
            animation_thread.daemon = True
            animation_thread.start()
            return animation_thread

        anim_thread = show_install_animation(package)
        
        try:

            result = subprocess.run([
                sys.executable, '-m', 'pip', 'install', package, '--quiet'
            ], capture_output=True, text=True)

            show_install_animation.running = False
            time.sleep(0.2)
            
            if result.returncode == 0:
                print(f"\r   Berhasil install {package}!")
            else:
                print(f"\r   Gagal install {package}")
                print(f"      Error: {result.stderr}")
                return False
                
        except Exception as e:
            show_install_animation.running = False
            print(f"\r   Error installing {package}: {e}")
            return False
    
    print("\nSemua package berhasil diinstall!")
    print("Starting Crypto Tracker...\n")
    time.sleep(1)
    return True

def show_welcome_screen():
    """Welcome"""
    try:
        from rich.console import Console
        from rich.panel import Panel
        from rich.text import Text
        from rich.align import Align
        from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
        
        console = Console()
        console.clear()
        
        welcome_text = Text()
        welcome_text.append("CRYPTO TRACKER", style="bold bright_green")
        welcome_text.append(" v2.0", style="dim bright_white")
        welcome_text.append("\n\n")
        welcome_text.append("Dibuat oleh: ", style="dim white")
        welcome_text.append("M. Imam Iryunullah", style="bold bright_magenta")
        welcome_text.append("\n")
        welcome_text.append("Real-time cryptocurrency tracker", style="bright_cyan")
        
        welcome_panel = Panel(
            Align.center(welcome_text),
            title="[bold bright_magenta]SELAMAT DATANG[/bold bright_magenta]",
            border_style="bright_magenta"
        )
        
        console.print(welcome_panel)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            console=console
        ) as progress:
            init_task = progress.add_task("[bright_green]Memulai aplikasi...", total=50)
            
            for i in range(50):
                if i < 15:
                    progress.update(init_task, description="[bright_blue]Loading dependencies...", advance=1)
                elif i < 30:
                    progress.update(init_task, description="[bright_yellow]Setup interface...", advance=1)
                elif i < 45:
                    progress.update(init_task, description="[bright_green]Setup koneksi...", advance=1)
                else:
                    progress.update(init_task, description="[bright_magenta]Siap launch!", advance=1)
                time.sleep(0.04)
        
    except ImportError:
 
        print("CRYPTO TRACKER v2.0")
        print("Dibuat oleh: M. Imam Iryunullah")
        print("Initializing...")

if __name__ == "__main__":
    try:
 
        if not check_and_install_dependencies():
            print("Gagal install required packages. Install manual:")
            print("   pip install requests rich")
            sys.exit(1)

        import requests
        from rich.console import Console

        show_welcome_screen()

        tracker = CryptoTrackerGenZ()
        tracker.run()
        
    except KeyboardInterrupt:
        print("\nInstallasi dibatalkan.")
        sys.exit(0)
    except Exception as e:
        print(f"Unexpected error: {e}")
        print("Coba install manual: pip install requests rich")
        sys.exit(1)