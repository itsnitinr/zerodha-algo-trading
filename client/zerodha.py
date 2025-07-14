import requests
from pyotp import TOTP
from dotenv import load_dotenv
import os
from typing import Optional
from utils.logger import get_logger, log_success, log_error, log_warning, log_info, log_step, log_api_call


class ZerodhaClient:
    """Handle Zerodha Kite authentication including login and 2FA."""
    
    def __init__(self, user_id: Optional[str] = None, password: Optional[str] = None, totp_key: Optional[str] = None):
        """
        Initialize ZerodhaAuth with credentials.
        
        Args:
            user_id: Zerodha user ID (if None, will load from environment)
            password: User password (if None, will load from environment)
            totp_key: TOTP secret key (if None, will load from environment)
        """
        self.logger = get_logger("zerodha_client")
        
        log_step("Initialization", "Starting Zerodha client setup")
        
        # Load environment variables
        load_dotenv()
        log_info("Environment variables loaded")
        
        self.user_id = user_id or os.getenv('USER_ID')
        self.password = password or os.getenv('PASSWORD')
        self.totp_key = totp_key or os.getenv('TOTP_KEY')
        
        # Log credential status (without exposing actual values)
        if self.user_id:
            log_info(f"User ID loaded: {self.user_id[:3]}***")
        if self.password:
            log_info("Password loaded successfully")
        if self.totp_key:
            log_info("TOTP key loaded successfully")
        
        if not all([self.user_id, self.password, self.totp_key]):
            log_error("Missing required credentials")
            raise ValueError("Missing required credentials. Provide user_id, password, and totp_key either as parameters or environment variables.")
        
        log_success("All credentials validated successfully")
        
        self.session = requests.Session()
        self.login_url = "https://kite.zerodha.com/api/login"
        self.totp_url = "https://kite.zerodha.com/api/twofa"
        self.enctoken = None
        
        log_info("Session initialized and endpoints configured")
    
    def login(self) -> requests.Session:
        """
        Perform complete login flow including 2FA and return authenticated session.
        
        Returns:
            requests.Session: Authenticated session ready for API calls with Authorization header set
            
        Raises:
            requests.RequestException: If login or 2FA fails
            ValueError: If response format is unexpected or enctoken not found
        """
        log_step("Authentication", "Starting complete login flow")
        
        try:
            # Step 1: Initial login
            log_step("Login Step 1", "Sending initial login request")
            login_data = {
                "user_id": self.user_id,
                "password": self.password
            }
            
            log_api_call("POST", self.login_url)
            response = self.session.post(self.login_url, data=login_data)
            log_api_call("POST", self.login_url, response.status_code)
            
            response.raise_for_status()
            log_success("Initial login request successful")
            
            response_data = response.json()
            if 'data' not in response_data or 'request_id' not in response_data['data']:
                log_error("Invalid login response format - missing data or request_id")
                raise ValueError("Unexpected login response format")
            
            request_id = response_data['data']['request_id']
            log_info(f"Request ID received: {request_id[:8]}...")
            
            # Step 2: 2FA verification
            log_step("Login Step 2", "Generating TOTP and sending 2FA request")
            twofa_code = TOTP(self.totp_key).now()
            log_info(f"TOTP code generated: {twofa_code[:2]}****")
            
            totp_data = {
                "request_id": request_id,
                "twofa_value": twofa_code,
                "user_id": self.user_id
            }
            
            log_api_call("POST", self.totp_url)
            response = self.session.post(self.totp_url, data=totp_data)
            log_api_call("POST", self.totp_url, response.status_code)
            
            response.raise_for_status()
            log_success("2FA verification successful")
            
            # Step 3: Extract enctoken from cookies and set authorization header
            log_step("Login Step 3", "Extracting enctoken and setting up authorization")
            enctoken_cookie = self.session.cookies.get('enctoken')
            if not enctoken_cookie:
                log_error("enctoken not found in cookies after authentication")
                raise ValueError("enctoken not found in cookies after authentication")
            
            self.enctoken = enctoken_cookie
            log_info(f"Enctoken extracted: {self.enctoken[:10]}...")
            
            # Set authorization header for all subsequent requests
            headers = {"Authorization": f"enctoken {self.enctoken}"}
            self.session.headers.update(headers)
            log_success("Authorization header configured for session")
            
            log_success("🎉 Complete authentication flow successful! Session ready for trading")
            return self.session
            
        except requests.RequestException as e:
            log_error(f"Network error during authentication: {str(e)}")
            raise
        except Exception as e:
            log_error(f"Unexpected error during authentication: {str(e)}")
            raise
    
    def get_authenticated_session(self) -> requests.Session:
        """
        Convenience method to get authenticated session.
        
        Returns:
            requests.Session: Authenticated session
        """
        log_info("Getting authenticated session")
        if self.enctoken and self.session.headers.get('Authorization'):
            log_info("Using existing authenticated session")
            return self.session
        else:
            log_info("No existing session found, performing fresh login")
            return self.login()
    
    def get_enctoken(self) -> Optional[str]:
        """
        Get the current enctoken.
        
        Returns:
            str: The enctoken if available, None if not authenticated yet
        """
        if self.enctoken:
            log_info(f"Returning enctoken: {self.enctoken[:10]}...")
        else:
            log_warning("No enctoken available - authentication required")
        return self.enctoken 