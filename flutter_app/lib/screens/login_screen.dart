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
  // Empty by default: farmers enter their own registered phone/email & password
  final _emailCtrl = TextEditingController();
  final _passwordCtrl = TextEditingController();
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
      setState(() => _error = 'Please enter your registered mobile number or email and password.');
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
      setState(() => _error = e.message);
    } catch (_) {
      setState(() => _error = 'Could not reach server. Please check your network connection.');
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

  Future<void> _showForgotPasswordDialog() async {
    final l10n = AppLocalizations.of(context);
    final resetCtrl = TextEditingController(text: _emailCtrl.text);
    await showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text(l10n.text('forgot_password')),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(l10n.text('forgot_password_desc'), style: const TextStyle(fontSize: 13, color: AppTheme.textMuted)),
            const SizedBox(height: 16),
            TextField(
              controller: resetCtrl,
              decoration: InputDecoration(
                labelText: l10n.text('email_or_phone'),
                prefixIcon: const Icon(Icons.contact_mail_outlined),
              ),
            ),
          ],
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: Text(l10n.text('cancel'))),
          FilledButton(
            onPressed: () async {
              final term = resetCtrl.text.trim();
              if (term.isEmpty) return;
              Navigator.pop(ctx);
              try {
                final res = await ApiClient.instance.forgotPassword(term);
                if (!mounted) return;
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(
                    content: Text(res['message'] ?? l10n.text('reset_instruction')),
                    backgroundColor: AppTheme.primaryGreen,
                  ),
                );
              } catch (e) {
                if (!mounted) return;
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(
                    content: Text(e.toString()),
                    backgroundColor: Colors.red.shade700,
                  ),
                );
              }
            },
            child: Text(l10n.text('submit')),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    return Scaffold(
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 24.0, vertical: 20.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              const SizedBox(height: 16),
              Center(
                child: Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: AppTheme.lightGreen,
                    shape: BoxShape.circle,
                  ),
                  child: const Icon(Icons.agriculture_rounded, size: 52, color: AppTheme.primaryGreen),
                ),
              ),
              const SizedBox(height: 16),
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
              const SizedBox(height: 28),
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
                  hintText: 'e.g., 9876543210 or farmer@example.com',
                  prefixIcon: const Icon(Icons.person_outline_rounded),
                ),
              ),
              const SizedBox(height: 16),
              TextField(
                controller: _passwordCtrl,
                obscureText: _obscure,
                decoration: InputDecoration(
                  labelText: l10n.text('password'),
                  hintText: 'Enter your password',
                  prefixIcon: const Icon(Icons.lock_outline_rounded),
                  suffixIcon: IconButton(
                    icon: Icon(_obscure ? Icons.visibility_outlined : Icons.visibility_off_outlined),
                    onPressed: () => setState(() => _obscure = !_obscure),
                  ),
                ),
              ),
              const SizedBox(height: 4),
              Align(
                alignment: Alignment.centerRight,
                child: TextButton(
                  onPressed: _showForgotPasswordDialog,
                  child: Text(l10n.text('forgot_password'), style: const TextStyle(fontSize: 13)),
                ),
              ),
              const SizedBox(height: 12),
              FilledButton(
                onPressed: _isLoading ? null : _handleLogin,
                child: _isLoading
                    ? const SizedBox(height: 22, width: 22, child: CircularProgressIndicator(strokeWidth: 2.5, color: Colors.white))
                    : Text(l10n.text('login_btn')),
              ),
              const SizedBox(height: 20),

              // Distinct Card for New Farmers
              Card(
                color: AppTheme.lightGreen.withOpacity(0.4),
                elevation: 0,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12),
                  side: BorderSide(color: AppTheme.primaryGreen.withOpacity(0.25)),
                ),
                child: Padding(
                  padding: const EdgeInsets.all(16.0),
                  child: Column(
                    children: [
                      const Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Icon(Icons.person_add_alt_1_rounded, color: AppTheme.primaryGreen, size: 20),
                          SizedBox(width: 8),
                          Text(
                            'New to TN Fertilizer Optimizer?',
                            style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14, color: AppTheme.darkGreen),
                          ),
                        ],
                      ),
                      const SizedBox(height: 6),
                      const Text(
                        'Create a free farmer account to store your soil cards, farm records, and receive custom fertilizer advice.',
                        textAlign: TextAlign.center,
                        style: TextStyle(fontSize: 12, color: AppTheme.textMuted, height: 1.3),
                      ),
                      const SizedBox(height: 12),
                      SizedBox(
                        width: double.infinity,
                        child: OutlinedButton(
                          style: OutlinedButton.styleFrom(
                            side: const BorderSide(color: AppTheme.primaryGreen, width: 1.5),
                            padding: const EdgeInsets.symmetric(vertical: 12),
                          ),
                          onPressed: () {
                            Navigator.push(context, MaterialPageRoute(builder: (_) => const RegisterScreen()));
                          },
                          child: const Text(
                            'Register as New Farmer',
                            style: TextStyle(fontWeight: FontWeight.bold, color: AppTheme.primaryGreen),
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 16),

              // Bottom links
              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Text(l10n.text('no_account'), style: const TextStyle(color: AppTheme.textMuted, fontSize: 13)),
                  TextButton(
                    onPressed: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const RegisterScreen())),
                    child: Text(l10n.text('register_here'), style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                  ),
                ],
              ),
              Center(
                child: TextButton.icon(
                  onPressed: _isLoading ? null : _guestLogin,
                  icon: const Icon(Icons.explore_outlined, size: 16, color: AppTheme.textMuted),
                  label: const Text('Quick Demo Login (Guest Mode)', style: TextStyle(fontSize: 12, color: AppTheme.textMuted)),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
