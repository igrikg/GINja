#!/bin/bash
# Create Debian package with dynamic versioning

VERSION="${1:?Version required}"
PACKAGE_NAME="ginja_${VERSION}_amd64.deb"

mkdir -p pkg/DEBIAN
mkdir -p pkg/usr/bin
mkdir -p pkg/usr/share/applications
mkdir -p pkg/usr/share/pixmaps
mkdir -p pkg/opt/ginja

# Copy PyInstaller output
cp -r dist/GINja-Converter pkg/opt/ginja/
cp -r dist/GINja-Report pkg/opt/ginja/

# Create symlinks
ln -s /opt/ginja/GINja-Converter/GINja-Converter pkg/usr/bin/ginja-converter
ln -s /opt/ginja/GINja-Report/GINja-Report pkg/usr/bin/ginja-report

# Copy icon
cp themes/BNC_logo.png pkg/usr/share/pixmaps/ginja_logo.png

# Create control file with dynamic version
cat > pkg/DEBIAN/control <<EOF
Package: ginja
Version: $VERSION
Section: science
Priority: optional
Architecture: amd64
Maintainer: BNC
Description: Reflectivity Data Reduction and Reporting Tool
EOF

# Create desktop files
cat > pkg/usr/share/applications/ginja-converter.desktop <<'EOF'
[Desktop Entry]
Type=Application
Name=GINja Converter
Exec=ginja-converter
Icon=ginja_logo
Terminal=false
Categories=Science;Education;
EOF

cat > pkg/usr/share/applications/ginja-report.desktop <<'EOF'
[Desktop Entry]
Type=Application
Name=GINja Report
Exec=ginja-report
Icon=ginja_logo
Terminal=false
Categories=Science;Education;
EOF

# Build the .deb
dpkg-deb --build pkg "$PACKAGE_NAME"
echo "✓ Created $PACKAGE_NAME"
