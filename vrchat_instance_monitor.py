#!/usr/bin/env python3
"""
VRChat World Instance Monitor

このスクリプトは特定のVRChatワールドのアクティブインスタンス数と
各インスタンスのユーザー数を10分ごとに取得してテキストファイルに記録します。
"""

import os
import sys
import time
import json
import base64
import requests
from datetime import datetime
from typing import Dict, List, Optional
import logging
from pathlib import Path

# .envファイルから環境変数を読み込む
try:
    from dotenv import load_dotenv
    # スクリプトと同じディレクトリの.envファイルを読み込む
    env_path = Path(__file__).parent / '.env'
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
        print(f"環境変数を {env_path} から読み込みました")
    else:
        print("警告: .envファイルが見つかりません。環境変数が設定されていることを確認してください。")
except ImportError:
    print("警告: python-dotenvがインストールされていません。")
    print("pip install python-dotenv を実行してインストールしてください。")
    print("環境変数は手動で設定する必要があります。")

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('vrchat_monitor.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class VRChatAPI:
    """VRChat APIクライアント"""
    
    BASE_URL = "https://api.vrchat.cloud/api/1"
    COOKIE_FILE = "vrchat_auth_cookie.txt"
    
    def __init__(self, username: Optional[str] = None, password: Optional[str] = None):
        """
        初期化
        
        Args:
            username: VRChatユーザー名（環境変数VRCHAT_USERNAMEから取得可能）
            password: VRChatパスワード（環境変数VRCHAT_PASSWORDから取得可能）
        """
        self.username = username or os.getenv('VRCHAT_USERNAME')
        self.password = password or os.getenv('VRCHAT_PASSWORD')
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        
        # 保存されたcookieを読み込む
        self._load_cookie()
    
    def _load_cookie(self):
        """保存されたauth cookieを読み込む"""
        if os.path.exists(self.COOKIE_FILE):
            try:
                with open(self.COOKIE_FILE, 'r') as f:
                    cookie_data = json.load(f)
                    for cookie in cookie_data:
                        self.session.cookies.set(
                            cookie['name'],
                            cookie['value'],
                            domain=cookie.get('domain', '.vrchat.cloud')
                        )
                logger.info("保存されたcookieを読み込みました")
            except Exception as e:
                logger.warning(f"Cookie読み込みエラー: {e}")
    
    def _save_cookie(self):
        """auth cookieを保存する"""
        try:
            cookie_data = []
            for cookie in self.session.cookies:
                cookie_data.append({
                    'name': cookie.name,
                    'value': cookie.value,
                    'domain': cookie.domain
                })
            with open(self.COOKIE_FILE, 'w') as f:
                json.dump(cookie_data, f)
            logger.info("Cookieを保存しました")
        except Exception as e:
            logger.error(f"Cookie保存エラー: {e}")
    
    def authenticate(self) -> bool:
        """
        VRChat APIに認証する
        
        Returns:
            認証成功の場合True
        """
        if not self.username or not self.password:
            logger.error("ユーザー名またはパスワードが設定されていません")
            return False
        
        try:
            # Basic認証用のトークンを作成
            from urllib.parse import quote
            auth_string = f"{quote(self.username)}:{quote(self.password)}"
            auth_token = base64.b64encode(auth_string.encode()).decode()
            
            headers = {
                'Authorization': f'Basic {auth_token}'
            }
            
            response = self.session.get(
                f"{self.BASE_URL}/auth/user",
                headers=headers
            )
            
            if response.status_code == 200:
                logger.info("認証に成功しました")
                self._save_cookie()
                return True
            else:
                logger.error(f"認証失敗: {response.status_code} - {response.text}")
                return False
        
        except Exception as e:
            logger.error(f"認証エラー: {e}")
            return False
    
    def get_world_info(self, world_id: str) -> Optional[Dict]:
        """
        ワールド情報を取得する
        
        Args:
            world_id: ワールドID
            
        Returns:
            ワールド情報の辞書、失敗時はNone
        """
        try:
            response = self.session.get(f"{self.BASE_URL}/worlds/{world_id}")
            
            logger.debug(f"ワールド情報取得レスポンス: status={response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.debug(f"ワールド情報取得成功: name={data.get('name')}, occupants={data.get('occupants')}, instances_count={len(data.get('instances', []))}")
                
                # インスタンス情報の詳細ログ
                instances = data.get('instances', [])
                if instances:
                    logger.info(f"取得したインスタンス数: {len(instances)}")
                    logger.debug(f"インスタンスデータのサンプル: {instances[:3] if len(instances) > 3 else instances}")
                else:
                    logger.warning("インスタンスリストが空です")
                
                return data
            elif response.status_code == 401:
                logger.warning("認証が必要です。再認証を試みます...")
                if self.authenticate():
                    return self.get_world_info(world_id)
                return None
            else:
                logger.error(f"ワールド情報取得失敗: {response.status_code}")
                logger.error(f"レスポンス内容: {response.text[:500]}")
                return None
        
        except Exception as e:
            logger.error(f"ワールド情報取得エラー: {e}", exc_info=True)
            return None
    
    def get_instance_info(self, world_id: str, instance_id: str) -> Optional[Dict]:
        """
        インスタンス詳細情報を取得する
        
        Args:
            world_id: ワールドID
            instance_id: インスタンスID
            
        Returns:
            インスタンス情報の辞書、失敗時はNone
        """
        try:
            response = self.session.get(
                f"{self.BASE_URL}/worlds/{world_id}/{instance_id}"
            )
            
            logger.debug(f"インスタンス情報取得: instance={instance_id}, status={response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.debug(f"インスタンス詳細: n_users={data.get('n_users')}, type={data.get('type')}, full={data.get('full')}")
                return data
            elif response.status_code == 401:
                logger.warning("認証が必要です。再認証を試みます...")
                if self.authenticate():
                    return self.get_instance_info(world_id, instance_id)
                return None
            else:
                logger.warning(f"インスタンス情報取得失敗: {response.status_code} (Instance: {instance_id})")
                logger.debug(f"レスポンス内容: {response.text[:200]}")
                return None
        
        except Exception as e:
            logger.error(f"インスタンス情報取得エラー: {e}")
            return None


class InstanceMonitor:
    """インスタンス監視クラス"""
    
    def __init__(self, world_id: str, output_file: str = "vrchat_instances.txt"):
        """
        初期化
        
        Args:
            world_id: 監視するワールドID
            output_file: 出力ファイル名
        """
        self.world_id = world_id
        self.output_file = output_file
        self.api = VRChatAPI()
    
    def collect_data(self) -> Optional[Dict]:
        """
        現在のインスタンスデータを収集する
        
        Returns:
            収集したデータの辞書、失敗時はNone
        """
        logger.info(f"ワールド {self.world_id} のデータを収集中...")
        
        # ワールド情報を取得
        world_info = self.api.get_world_info(self.world_id)
        if not world_info:
            logger.error("ワールド情報の取得に失敗しました")
            return None
        
        # レスポンスの検証
        if not isinstance(world_info, dict):
            logger.error(f"ワールド情報が辞書型ではありません: type={type(world_info)}")
            return None
        
        # インスタンスリストを取得
        instances = world_info.get('instances', [])
        
        # インスタンスリストの検証
        if not isinstance(instances, list):
            logger.error(f"インスタンスリストがリスト型ではありません: type={type(instances)}")
            logger.error(f"instances値: {instances}")
            instances = []
        
        logger.info(f"ワールド情報: name={world_info.get('name')}, occupants={world_info.get('occupants')}")
        logger.info(f"取得したインスタンス数: {len(instances)}")
        
        # データ構造
        data = {
            'timestamp': datetime.now().isoformat(),
            'world_id': self.world_id,
            'world_name': world_info.get('name', 'Unknown'),
            'total_occupants': world_info.get('occupants', 0),
            'public_occupants': world_info.get('publicOccupants', 0),
            'private_occupants': world_info.get('privateOccupants', 0),
            'active_instances': len(instances),
            'instances': []
        }
        
        # インスタンスが0の場合の警告
        if len(instances) == 0:
            logger.warning("アクティブなインスタンスが見つかりませんでした")
            logger.warning(f"ワールド情報の全フィールド: {list(world_info.keys())}")
            logger.warning(f"occupants={world_info.get('occupants')}, publicOccupants={world_info.get('publicOccupants')}")
        
        # 各インスタンスの詳細情報を取得
        for idx, instance in enumerate(instances):
            logger.debug(f"処理中のインスタンス #{idx + 1}: {instance}")
            
            # インスタンスデータの検証
            if not instance:
                logger.warning(f"インスタンス #{idx + 1} が空です")
                continue
            
            if not isinstance(instance, (list, tuple)):
                logger.warning(f"インスタンス #{idx + 1} がリストまたはタプルではありません: type={type(instance)}, value={instance}")
                continue
            
            if len(instance) < 2:
                logger.warning(f"インスタンス #{idx + 1} の要素数が不足しています: len={len(instance)}, value={instance}")
                continue
            
            instance_id = instance[0]
            user_count = instance[1]
            
            logger.info(f"インスタンス #{idx + 1}: ID={instance_id}, ユーザー数={user_count}")
            
            # インスタンス詳細を取得（オプション）
            instance_detail = self.api.get_instance_info(self.world_id, instance_id)
            
            instance_data = {
                'instance_id': instance_id,
                'user_count': user_count
            }
            
            if instance_detail:
                instance_data.update({
                    'n_users': instance_detail.get('n_users', 0),
                    'capacity': instance_detail.get('capacity', 0),
                    'type': instance_detail.get('type', 'unknown'),
                    'full': instance_detail.get('full', False),
                    'platforms': instance_detail.get('platforms', {})
                })
            else:
                logger.warning(f"インスタンス #{idx + 1} の詳細情報を取得できませんでした")
            
            data['instances'].append(instance_data)
            
            # レート制限対策
            time.sleep(0.5)
        
        logger.info(f"データ収集完了: {len(data['instances'])}個のインスタンス情報を取得")
        
        # 最終検証
        if data['total_occupants'] > 0 and len(data['instances']) == 0:
            logger.error("警告: ユーザーが存在するのにインスタンス情報が取得できませんでした")
            logger.error("これはAPIレスポンスの形式が予想と異なる可能性があります")
        
        return data
    
    def save_data(self, data: Dict):
        """
        データをファイルに保存する
        
        Args:
            data: 保存するデータ
        """
        try:
            with open(self.output_file, 'a', encoding='utf-8') as f:
                # ヘッダー行
                f.write(f"\n{'='*80}\n")
                f.write(f"収集日時: {data['timestamp']}\n")
                f.write(f"ワールド名: {data['world_name']}\n")
                f.write(f"ワールドID: {data['world_id']}\n")
                f.write(f"総ユーザー数: {data['total_occupants']}\n")
                f.write(f"パブリックユーザー数: {data['public_occupants']}\n")
                f.write(f"プライベートユーザー数: {data['private_occupants']}\n")
                f.write(f"アクティブインスタンス数: {data['active_instances']}\n")
                f.write(f"{'-'*80}\n")
                
                # インスタンス詳細
                if data['instances']:
                    for i, instance in enumerate(data['instances'], 1):
                        f.write(f"\nインスタンス #{i}\n")
                        f.write(f"  ID: {instance['instance_id']}\n")
                        f.write(f"  ユーザー数: {instance['user_count']}\n")
                        
                        if 'type' in instance:
                            f.write(f"  タイプ: {instance['type']}\n")
                        if 'capacity' in instance:
                            f.write(f"  最大収容人数: {instance['capacity']}\n")
                        if 'full' in instance:
                            f.write(f"  満員: {'はい' if instance['full'] else 'いいえ'}\n")
                        if 'platforms' in instance and instance['platforms']:
                            f.write(f"  プラットフォーム別: {instance['platforms']}\n")
                else:
                    f.write(f"\n※ アクティブなインスタンスが見つかりませんでした\n")
                
                f.write(f"\n{'='*80}\n")
            
            logger.info(f"データを {self.output_file} に保存しました")
        
        except Exception as e:
            logger.error(f"データ保存エラー: {e}", exc_info=True)
    
    def run(self, interval_minutes: int = 10):
        """
        監視を開始する
        
        Args:
            interval_minutes: データ収集間隔（分）
        """
        logger.info(f"インスタンス監視を開始します（間隔: {interval_minutes}分）")
        logger.info(f"対象ワールド: {self.world_id}")
        logger.info(f"出力ファイル: {self.output_file}")
        logger.info("Ctrl+Cで停止できます")
        
        # 初回認証
        if not self.api.authenticate():
            logger.error("認証に失敗しました。VRCHAT_USERNAMEとVRCHAT_PASSWORDを確認してください")
            return
        
        try:
            while True:
                # データ収集
                data = self.collect_data()
                
                if data:
                    # データ保存
                    self.save_data(data)
                else:
                    logger.warning("データ収集に失敗しました")
                
                # 次回実行まで待機
                logger.info(f"{interval_minutes}分後に次回収集を実行します...")
                time.sleep(interval_minutes * 60)
        
        except KeyboardInterrupt:
            logger.info("\n監視を停止しました")
        except Exception as e:
            logger.error(f"予期しないエラー: {e}", exc_info=True)


def main():
    """メイン関数"""
    # 環境変数から設定を取得
    world_id = os.getenv('VRCHAT_WORLD_ID', 'wrld_7bb60bf6-3c69-4039-a5d6-0cbbda092290')
    output_file = os.getenv('OUTPUT_FILE', 'vrchat_instances.txt')
    interval_minutes = int(os.getenv('INTERVAL_MINUTES', '10'))
    
    # デバッグモードの確認
    debug_mode = os.getenv('DEBUG', 'false').lower() == 'true'
    if debug_mode:
        logger.setLevel(logging.DEBUG)
        logger.info("デバッグモードが有効です")
    
    logger.info(f"設定: world_id={world_id}, output_file={output_file}, interval={interval_minutes}分")
    
    # 監視開始
    monitor = InstanceMonitor(world_id, output_file)
    monitor.run(interval_minutes)


if __name__ == '__main__':
    main()
