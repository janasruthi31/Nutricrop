import 'package:flutter/material.dart';
import '../l10n/app_localizations.dart';
import '../services/api_client.dart';
import '../theme/app_theme.dart';
import 'login_screen.dart';

class ProfileScreen extends StatefulWidget {
  const ProfileScreen({super.key});

  @override
  State<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends State<ProfileScreen> {
  final _nameCtrl = TextEditingController();
  final _phoneCtrl = TextEditingController();
  String _district = 'Thanjavur';
  String _email = '';
  String _userId = '';
  bool _isLoading = true;
  bool _isSaving = false;

  static const List<String> tnDistricts = [
    'Thanjavur', 'Tiruvarur', 'Nagapattinam', 'Mayiladuthurai', 'Cuddalore',
    'Coimbatore', 'Tiruppur', 'Erode', 'Madurai', 'Dindigul', 'Salem', 'Trichy',
    'Ariyalur', 'Chengalpattu', 'Chennai', 'Dharmapuri', 'Kallakurichi', 'Kancheepuram',
    'Kanniyakumari', 'Karur', 'Krishnagiri', 'Namakkal', 'Nilgiris', 'Perambalur',
    'Pudukkottai', 'Ramanathapuram', 'Ranipet', 'Sivaganga', 'Tenkasi', 'Theni',
    'Thoothukudi', 'Tiruchirappalli', 'Tirunelveli', 'Tirupathur', 'Tiruvallur',
    'Tiruvannamalai', 'Vellore', 'Viluppuram', 'Virudhunagar'
  ];

  @override
  void initState() {
    super.initState();
    _loadProfile();
  }

  Future<void> _loadProfile() async {
    setState(() => _isLoading = true);
    try {
      final p = await ApiClient.instance.getProfile();
      setState(() {
        _userId = p['user_id'] ?? 'farmer_001';
        _email = p['email'] ?? '';
        _nameCtrl.text = p['full_name'] ?? 'Farmer';
        _phoneCtrl.text = p['phone'] ?? '';
        if (p['district'] != null && tnDistricts.contains(p['district'])) {
          _district = p['district'];
        }
      });
    } catch (_) {}
    finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  Future<void> _saveProfile() async {
    setState(() => _isSaving = true);
    try {
      await ApiClient.instance.updateProfile({
        'full_name': _nameCtrl.text.trim(),
        'phone': _phoneCtrl.text.trim(),
        'district': _district,
      });
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Profile updated successfully!')));
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Update failed: $e')));
    } finally {
      if (mounted) setState(() => _isSaving = false);
    }
  }

  void _logout() {
    ApiClient.instance.clearSession();
    Navigator.pushAndRemoveUntil(
      context,
      MaterialPageRoute(builder: (_) => const LoginScreen()),
      (route) => false,
    );
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    return Scaffold(
      appBar: AppBar(title: Text(l10n.text('profile'))),
      body: SafeArea(
        child: _isLoading
            ? const Center(child: CircularProgressIndicator())
            : SingleChildScrollView(
                padding: const EdgeInsets.all(22.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    Center(
                      child: Column(
                        children: [
                          CircleAvatar(
                            radius: 40,
                            backgroundColor: AppTheme.lightGreen,
                            child: const Icon(Icons.person_rounded, size: 50, color: AppTheme.primaryGreen),
                          ),
                          const SizedBox(height: 12),
                          Text(_nameCtrl.text, style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
                          Text(_email, style: const TextStyle(fontSize: 13, color: AppTheme.textMuted)),
                          const SizedBox(height: 4),
                          Text('ID: $_userId', style: const TextStyle(fontSize: 11, color: Colors.grey)),
                        ],
                      ),
                    ),
                    const SizedBox(height: 28),
                    TextField(
                      controller: _nameCtrl,
                      decoration: InputDecoration(labelText: l10n.text('full_name'), prefixIcon: const Icon(Icons.badge_outlined)),
                    ),
                    const SizedBox(height: 14),
                    TextField(
                      controller: _phoneCtrl,
                      keyboardType: TextInputType.phone,
                      decoration: const InputDecoration(labelText: 'Phone Number', prefixIcon: Icon(Icons.phone_outlined)),
                    ),
                    const SizedBox(height: 14),
                    DropdownButtonFormField<String>(
                      value: tnDistricts.contains(_district) ? _district : 'Thanjavur',
                      decoration: InputDecoration(labelText: l10n.text('district'), prefixIcon: const Icon(Icons.location_on_outlined)),
                      items: tnDistricts.toSet().map((d) => DropdownMenuItem(value: d, child: Text(d))).toList(),
                      onChanged: (v) => setState(() => _district = v ?? 'Thanjavur'),
                    ),
                    const SizedBox(height: 24),
                    FilledButton(
                      onPressed: _isSaving ? null : _saveProfile,
                      child: Text(_isSaving ? 'Saving...' : l10n.text('save')),
                    ),
                    const SizedBox(height: 14),
                    OutlinedButton.icon(
                      onPressed: _logout,
                      icon: const Icon(Icons.logout_rounded, color: Colors.red),
                      label: Text(l10n.text('logout'), style: const TextStyle(color: Colors.red)),
                      style: OutlinedButton.styleFrom(side: const BorderSide(color: Colors.red)),
                    ),
                  ],
                ),
              ),
      ),
    );
  }
}
