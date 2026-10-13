import 'package:flutter/material.dart';
import '../l10n/app_localizations.dart';
import '../services/api_client.dart';
import '../theme/app_theme.dart';
import 'main_navigation_shell.dart';
import 'register_screen.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _emailCtrl = TextEditingController(text: 'farmer_001@tnsih.agri');
  final _passwordCtrl = TextEditingController(text: 'FarmerPass123');
  bool _obscure = true;
  bool _isLoading = false;
  String? _error;

  @override
  void dispose() {
    _emailCtrl.dispose();
    _passwordCtrl.dispose();
    super.dispose();
  }

  Future<void> _handleLogin() async {
    final email = _emailCtrl.text.trim();
    final pwd = _passwordCtrl.text;
    if (email.isEmpty || pwd.isEmpty) {
      setState(() => _error = 'Please fill in both email and password.');
      return;
    }

    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      await ApiClient.instance.login(email: email, password: pwd);
      if (!mounted) return;
      Navigator.pushReplacement(context, MaterialPageRoute(builder: (_) => const MainNavigationShell()));
    } on ApiException catch (e) {
      // If demo account doesn't exist yet, auto-register or offer guest mode
      if (email.contains('farmer_001')) {
        try {
          await ApiClient.instance.register(
            email: email,
            password: pwd,
            fullName: 'Tamil Nadu Farmer',
            district: 'Thanjavur',
            preferredLanguage: globalLocaleNotifier.locale.languageCode,
          );
          if (!mounted) return;
          Navigator.pushReplacement(context, MaterialPageRoute(builder: (_) => const MainNavigationShell()));
          return;
        } catch (_) {}
      }
      setState(() => _error = e.message);
    } catch (_) {
      setState(() => _error = 'Could not reach server. Please check connection.');
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  void _guestLogin() {
    ApiClient.instance.setSession('demo_token', 'farmer_001', {
      'user_id': 'farmer_001',
      'email': 'farmer_001@tnsih.agri',
      'full_name': 'Thanjavur Farmer',
      'district': 'Thanjavur',
    });
    Navigator.pushReplacement(context, MaterialPageRoute(builder: (_) => const MainNavigationShell()));
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    return Scaffold(
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              const SizedBox(height: 24),
              Center(
                child: Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: AppTheme.lightGreen,
                    shape: BoxShape.circle,
                  ),
                  child: const Icon(Icons.agriculture_rounded, size: 54, color: AppTheme.primaryGreen),
                ),
              ),
              const SizedBox(height: 20),
              Text(
                l10n.text('login_title'),
                textAlign: TextAlign.center,
                style: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold, color: AppTheme.textDark),
              ),
              const SizedBox(height: 6),
              Text(
                l10n.text('login_subtitle'),
                textAlign: TextAlign.center,
                style: const TextStyle(fontSize: 13, color: AppTheme.textMuted),
              ),
              const SizedBox(height: 32),
              if (_error != null) ...[
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: const Color(0xFFFFEBEE),
                    borderRadius: BorderRadius.circular(10),
                    border: Border.all(color: const Color(0xFFFFCDD2)),
                  ),
                  child: Row(
                    children: [
                      const Icon(Icons.error_outline_rounded, color: Color(0xFFD32F2F)),
                      const SizedBox(width: 10),
                      Expanded(child: Text(_error!, style: const TextStyle(color: Color(0xFFC62828), fontSize: 13))),
                    ],
                  ),
                ),
                const SizedBox(height: 18),
              ],
              TextField(
                controller: _emailCtrl,
                keyboardType: TextInputType.emailAddress,
                decoration: InputDecoration(
                  labelText: l10n.text('email_or_phone'),
                  prefixIcon: const Icon(Icons.person_outline_rounded),
                ),
              ),
              const SizedBox(height: 16),
              TextField(
                controller: _passwordCtrl,
                obscureText: _obscure,
                decoration: InputDecoration(
                  labelText: l10n.text('password'),
                  prefixIcon: const Icon(Icons.lock_outline_rounded),
                  suffixIcon: IconButton(
                    icon: Icon(_obscure ? Icons.visibility_outlined : Icons.visibility_off_outlined),
                    onPressed: () => setState(() => _obscure = !_obscure),
                  ),
                ),
              ),
              const SizedBox(height: 26),
              FilledButton(
                onPressed: _isLoading ? null : _handleLogin,
                child: _isLoading
                    ? const SizedBox(height: 22, width: 22, child: CircularProgressIndicator(strokeWidth: 2.5, color: Colors.white))
                    : Text(l10n.text('login_btn')),
              ),
              const SizedBox(height: 14),
              OutlinedButton(
                onPressed: _isLoading ? null : _guestLogin,
                child: const Text('Quick Demo Login (Guest Mode)'),
              ),
              const SizedBox(height: 28),
              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Text(l10n.text('no_account'), style: const TextStyle(color: AppTheme.textMuted)),
                  TextButton(
                    onPressed: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const RegisterScreen())),
                    child: Text(l10n.text('register_here'), style: const TextStyle(fontWeight: FontWeight.bold)),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}
