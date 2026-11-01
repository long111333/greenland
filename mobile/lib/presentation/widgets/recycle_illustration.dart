import 'dart:math' as math;

import 'package:flutter/material.dart';

import '../../config/theme.dart';

/// Line-art recycle bin + floating waste items (Start screen).
class RecycleIllustration extends StatelessWidget {
  const RecycleIllustration({super.key, this.size = 260});

  final double size;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: size,
      height: size,
      child: CustomPaint(painter: _RecycleScenePainter()),
    );
  }
}

class _RecycleScenePainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width / 2, size.height / 2 + 6);

    final blob = Paint()..color = AppColors.mint.withOpacity(0.85);
    canvas.drawOval(
      Rect.fromCenter(center: center, width: size.width * 0.72, height: size.height * 0.62),
      blob,
    );

    _drawBin(canvas, center, size);
    _drawFloatingItems(canvas, size);
  }

  void _drawBin(Canvas canvas, Offset center, Size size) {
    final stroke = Paint()
      ..color = AppColors.primary
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2.4
      ..strokeCap = StrokeCap.round
      ..strokeJoin = StrokeJoin.round;

    final fill = Paint()..color = Colors.white;
    final binW = size.width * 0.34;
    final binH = size.height * 0.38;
    final rect = RRect.fromRectAndRadius(
      Rect.fromCenter(center: center.translate(0, 8), width: binW, height: binH),
      const Radius.circular(22),
    );
    canvas.drawRRect(rect, fill);
    canvas.drawRRect(rect, stroke);

    final lid = RRect.fromRectAndRadius(
      Rect.fromCenter(
        center: Offset(center.dx, center.dy - binH / 2 + 10),
        width: binW * 0.72,
        height: 10,
      ),
      const Radius.circular(6),
    );
    canvas.drawRRect(lid, stroke);

    _drawRecycleMark(canvas, center.translate(0, 10), binW * 0.22, stroke);
  }

  void _drawRecycleMark(Canvas canvas, Offset center, double radius, Paint stroke) {
    for (var i = 0; i < 3; i++) {
      final start = -math.pi / 2 + i * 2 * math.pi / 3;
      final path = Path();
      path.addArc(
        Rect.fromCircle(center: center, radius: radius),
        start,
        1.55,
      );
      canvas.drawPath(path, stroke);
      final tip = Offset(
        center.dx + radius * math.cos(start + 1.55),
        center.dy + radius * math.sin(start + 1.55),
      );
      final dir = start + 1.55;
      final arrow = Path()
        ..moveTo(tip.dx, tip.dy)
        ..lineTo(
          tip.dx - 7 * math.cos(dir - 0.7),
          tip.dy - 7 * math.sin(dir - 0.7),
        )
        ..moveTo(tip.dx, tip.dy)
        ..lineTo(
          tip.dx - 7 * math.cos(dir + 2.4),
          tip.dy - 7 * math.sin(dir + 2.4),
        );
      canvas.drawPath(arrow, stroke);
    }
  }

  void _drawFloatingItems(Canvas canvas, Size size) {
    final stroke = Paint()
      ..color = AppColors.primary
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2.1
      ..strokeCap = StrokeCap.round
      ..strokeJoin = StrokeJoin.round;

    _drawBottle(canvas, Offset(size.width * 0.16, size.height * 0.38), 16, stroke);
    _drawCan(canvas, Offset(size.width * 0.20, size.height * 0.68), 13, stroke);
    _drawBox(canvas, Offset(size.width * 0.70, size.height * 0.20), 15, stroke);
    _drawBag(canvas, Offset(size.width * 0.82, size.height * 0.40), 16, stroke);
    _drawBottle(canvas, Offset(size.width * 0.84, size.height * 0.62), 14, stroke);
  }

  void _drawBottle(Canvas canvas, Offset c, double s, Paint p) {
    final body = RRect.fromRectAndRadius(
      Rect.fromCenter(center: c.translate(0, 4), width: s * 0.7, height: s * 1.4),
      const Radius.circular(5),
    );
    canvas.drawRRect(body, p);
    canvas.drawRRect(
      RRect.fromRectAndRadius(
        Rect.fromCenter(center: c.translate(0, -s * 0.72), width: s * 0.28, height: s * 0.28),
        const Radius.circular(2),
      ),
      p,
    );
  }

  void _drawCan(Canvas canvas, Offset c, double s, Paint p) {
    canvas.drawRRect(
      RRect.fromRectAndRadius(
        Rect.fromCenter(center: c, width: s * 0.9, height: s * 1.25),
        const Radius.circular(4),
      ),
      p,
    );
    canvas.drawArc(
      Rect.fromCenter(center: c.translate(0, -s * 0.52), width: s * 0.9, height: 6),
      0,
      math.pi,
      false,
      p,
    );
  }

  void _drawBox(Canvas canvas, Offset c, double s, Paint p) {
    canvas.drawRRect(
      RRect.fromRectAndRadius(
        Rect.fromCenter(center: c, width: s * 1.35, height: s * 1.15),
        const Radius.circular(3),
      ),
      p,
    );
    canvas.drawLine(c.translate(-s * 0.2, -s * 0.55), c.translate(-s * 0.2, s * 0.55), p);
  }

  void _drawBag(Canvas canvas, Offset c, double s, Paint p) {
    final path = Path()
      ..moveTo(c.dx - s * 0.55, c.dy - s * 0.15)
      ..lineTo(c.dx - s * 0.5, c.dy + s * 0.7)
      ..quadraticBezierTo(c.dx, c.dy + s * 0.9, c.dx + s * 0.5, c.dy + s * 0.7)
      ..lineTo(c.dx + s * 0.55, c.dy - s * 0.15)
      ..close();
    canvas.drawPath(path, p);
    canvas.drawArc(
      Rect.fromCenter(center: c.translate(-s * 0.22, -s * 0.22), width: s * 0.45, height: s * 0.45),
      math.pi,
      2.4,
      false,
      p,
    );
    canvas.drawArc(
      Rect.fromCenter(center: c.translate(s * 0.22, -s * 0.22), width: s * 0.45, height: s * 0.45),
      math.pi,
      2.4,
      false,
      p,
    );
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}

/// Line-style waste category glyphs used on Overview cards.
class CategoryGlyph extends StatelessWidget {
  const CategoryGlyph({super.key, required this.classId, this.size = 36});

  final String classId;
  final double size;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: size,
      height: size,
      child: CustomPaint(painter: _CategoryGlyphPainter(classId)),
    );
  }
}

class _CategoryGlyphPainter extends CustomPainter {
  _CategoryGlyphPainter(this.classId);

  final String classId;

  @override
  void paint(Canvas canvas, Size size) {
    final p = Paint()
      ..color = AppColors.primary
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1.8
      ..strokeCap = StrokeCap.round
      ..strokeJoin = StrokeJoin.round;
    final c = Offset(size.width / 2, size.height / 2);
    switch (classId) {
      case 'plastic':
        _bag(canvas, c, size.width * 0.36, p);
      case 'metal':
        _can(canvas, c, size.width * 0.32, p);
      case 'paper':
        _box(canvas, c, size.width * 0.34, p);
      default:
        _bin(canvas, c, size.width * 0.32, p);
    }
  }

  void _bag(Canvas canvas, Offset c, double s, Paint p) {
    final path = Path()
      ..moveTo(c.dx - s * 0.7, c.dy - s * 0.15)
      ..lineTo(c.dx - s * 0.62, c.dy + s * 0.85)
      ..quadraticBezierTo(c.dx, c.dy + s * 1.05, c.dx + s * 0.62, c.dy + s * 0.85)
      ..lineTo(c.dx + s * 0.7, c.dy - s * 0.15)
      ..close();
    canvas.drawPath(path, p);
    canvas.drawArc(Rect.fromCircle(center: c.translate(-s * 0.28, -s * 0.28), radius: s * 0.32), math.pi, 2.3, false, p);
    canvas.drawArc(Rect.fromCircle(center: c.translate(s * 0.28, -s * 0.28), radius: s * 0.32), math.pi, 2.3, false, p);
  }

  void _can(Canvas canvas, Offset c, double s, Paint p) {
    canvas.drawRRect(
      RRect.fromRectAndRadius(Rect.fromCenter(center: c, width: s * 1.15, height: s * 1.7), const Radius.circular(4)),
      p,
    );
    canvas.drawOval(Rect.fromCenter(center: c.translate(0, -s * 0.78), width: s * 1.15, height: 5), p);
  }

  void _box(Canvas canvas, Offset c, double s, Paint p) {
    canvas.drawRRect(
      RRect.fromRectAndRadius(Rect.fromCenter(center: c, width: s * 1.55, height: s * 1.3), const Radius.circular(3)),
      p,
    );
    canvas.drawLine(c.translate(0, -s * 0.65), c.translate(0, s * 0.65), p);
  }

  void _bin(Canvas canvas, Offset c, double s, Paint p) {
    canvas.drawRRect(
      RRect.fromRectAndRadius(Rect.fromCenter(center: c.translate(0, 2), width: s * 1.4, height: s * 1.35), const Radius.circular(4)),
      p,
    );
    canvas.drawLine(c.translate(-s * 0.85, -s * 0.55), c.translate(s * 0.85, -s * 0.55), p);
  }

  @override
  bool shouldRepaint(covariant _CategoryGlyphPainter oldDelegate) => oldDelegate.classId != classId;
}
