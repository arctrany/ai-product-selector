"""
Project Type Detection Module

Automatically detects project type based on files and structure.
"""

import os
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class ProjectTypeDetector:
    """Detects project type based on project structure and files."""
    
    def __init__(self, project_root: Path):
        """Initialize project detector."""
        self.project_root = Path(project_root)
    
    def detect_project_type(self) -> Tuple[str, float]:
        """
        Detect project type and return confidence score.
        
        Returns:
            Tuple of (project_type, confidence_score)
            confidence_score is between 0.0 and 1.0
        """
        detectors = [
            self._detect_java_spring_boot,
            self._detect_java_maven,
            self._detect_java_gradle,
            self._detect_nodejs,
            self._detect_python,
            self._detect_react,
            self._detect_vue,
            self._detect_angular,
            self._detect_go,
            self._detect_rust,
            self._detect_dotnet
        ]
        
        best_match = ("unknown", 0.0)
        
        for detector in detectors:
            try:
                project_type, confidence = detector()
                if confidence > best_match[1]:
                    best_match = (project_type, confidence)
            except Exception as e:
                logger.debug(f"Detector {detector.__name__} failed: {e}")
        
        return best_match
    
    def _detect_java_spring_boot(self) -> Tuple[str, float]:
        """Detect Java Spring Boot project."""
        confidence = 0.0
        
        # Check for Spring Boot indicators
        spring_indicators = [
            "src/main/java",
            "src/main/resources/application.yml",
            "src/main/resources/application.properties",
            "src/main/resources/application-*.yml",
            "src/main/resources/application-*.properties"
        ]
        
        # Check Maven pom.xml for Spring Boot
        pom_file = self.project_root / "pom.xml"
        if pom_file.exists():
            confidence += 0.3
            try:
                tree = ET.parse(pom_file)
                root = tree.getroot()
                
                # Remove namespace for easier searching
                for elem in root.iter():
                    if '}' in elem.tag:
                        elem.tag = elem.tag.split('}')[1]
                
                # Check for Spring Boot parent or dependencies
                spring_boot_found = False
                
                # Check parent
                parent = root.find('parent')
                if parent is not None:
                    group_id = parent.find('groupId')
                    artifact_id = parent.find('artifactId')
                    if (group_id is not None and group_id.text == 'org.springframework.boot' and
                        artifact_id is not None and artifact_id.text == 'spring-boot-starter-parent'):
                        spring_boot_found = True
                        confidence += 0.4
                
                # Check dependencies
                dependencies = root.find('dependencies')
                if dependencies is not None:
                    for dependency in dependencies.findall('dependency'):
                        group_id = dependency.find('groupId')
                        artifact_id = dependency.find('artifactId')
                        if (group_id is not None and group_id.text == 'org.springframework.boot'):
                            spring_boot_found = True
                            confidence += 0.2
                            break
                
                if not spring_boot_found:
                    # Not Spring Boot, reduce confidence significantly
                    confidence = max(0.0, confidence - 0.5)
                    
            except Exception as e:
                logger.debug(f"Failed to parse pom.xml: {e}")
        
        # Check Gradle build files for Spring Boot
        gradle_files = [
            self.project_root / "build.gradle",
            self.project_root / "build.gradle.kts"
        ]
        
        for gradle_file in gradle_files:
            if gradle_file.exists():
                confidence += 0.3
                try:
                    content = gradle_file.read_text()
                    if 'org.springframework.boot' in content or 'spring-boot' in content:
                        confidence += 0.4
                    else:
                        confidence = max(0.0, confidence - 0.5)
                except Exception as e:
                    logger.debug(f"Failed to read {gradle_file}: {e}")
                break
        
        # Check for Spring Boot specific files
        for indicator in spring_indicators:
            if (self.project_root / indicator).exists():
                confidence += 0.1
            # Check for pattern matches (like application-*.yml)
            elif '*' in indicator:
                pattern_path = Path(indicator.replace('*', ''))
                parent_dir = self.project_root / pattern_path.parent
                if parent_dir.exists():
                    pattern = pattern_path.name.replace('*', '')
                    matching_files = [f for f in parent_dir.iterdir() 
                                    if f.name.startswith(pattern.split('*')[0]) and 
                                       f.name.endswith(pattern.split('*')[-1])]
                    if matching_files:
                        confidence += 0.1
        
        # Check for @SpringBootApplication annotation
        java_files = list(self.project_root.rglob("*.java"))
        for java_file in java_files[:10]:  # Check first 10 Java files
            try:
                content = java_file.read_text()
                if '@SpringBootApplication' in content:
                    confidence += 0.3
                    break
            except Exception:
                continue
        
        return ("java-spring-boot", min(1.0, confidence))
    
    def _detect_java_maven(self) -> Tuple[str, float]:
        """Detect Java Maven project (non-Spring Boot)."""
        confidence = 0.0
        
        pom_file = self.project_root / "pom.xml"
        if pom_file.exists():
            confidence += 0.5
            
            # Check for Java source structure
            if (self.project_root / "src" / "main" / "java").exists():
                confidence += 0.3
            
            # Make sure it's not Spring Boot (already checked above)
            try:
                tree = ET.parse(pom_file)
                root = tree.getroot()
                
                # Remove namespace
                for elem in root.iter():
                    if '}' in elem.tag:
                        elem.tag = elem.tag.split('}')[1]
                
                # Check if it's NOT Spring Boot
                is_spring_boot = False
                parent = root.find('parent')
                if parent is not None:
                    group_id = parent.find('groupId')
                    artifact_id = parent.find('artifactId')
                    if (group_id is not None and group_id.text == 'org.springframework.boot'):
                        is_spring_boot = True
                
                dependencies = root.find('dependencies')
                if dependencies is not None:
                    for dependency in dependencies.findall('dependency'):
                        group_id = dependency.find('groupId')
                        if group_id is not None and group_id.text == 'org.springframework.boot':
                            is_spring_boot = True
                            break
                
                if is_spring_boot:
                    confidence = 0.0  # It's Spring Boot, not plain Maven
                    
            except Exception as e:
                logger.debug(f"Failed to parse pom.xml: {e}")
        
        return ("java-maven", confidence)
    
    def _detect_java_gradle(self) -> Tuple[str, float]:
        """Detect Java Gradle project (non-Spring Boot)."""
        confidence = 0.0
        
        gradle_files = [
            self.project_root / "build.gradle",
            self.project_root / "build.gradle.kts"
        ]
        
        for gradle_file in gradle_files:
            if gradle_file.exists():
                confidence += 0.5
                
                try:
                    content = gradle_file.read_text()
                    if 'java' in content or 'application' in content:
                        confidence += 0.2
                    
                    # Make sure it's not Spring Boot
                    if 'org.springframework.boot' in content or 'spring-boot' in content:
                        confidence = 0.0  # It's Spring Boot, not plain Gradle
                        
                except Exception as e:
                    logger.debug(f"Failed to read {gradle_file}: {e}")
                break
        
        # Check for Java source structure
        if (self.project_root / "src" / "main" / "java").exists():
            confidence += 0.3
        
        return ("java-gradle", confidence)
    
    def _detect_nodejs(self) -> Tuple[str, float]:
        """Detect Node.js project."""
        confidence = 0.0
        
        if (self.project_root / "package.json").exists():
            confidence += 0.6
        
        if (self.project_root / "node_modules").exists():
            confidence += 0.2
        
        if (self.project_root / "yarn.lock").exists() or (self.project_root / "package-lock.json").exists():
            confidence += 0.2
        
        return ("nodejs", confidence)
    
    def _detect_python(self) -> Tuple[str, float]:
        """Detect Python project."""
        confidence = 0.0
        
        python_indicators = [
            "requirements.txt",
            "setup.py",
            "pyproject.toml",
            "Pipfile",
            "environment.yml",
            "conda.yml"
        ]
        
        for indicator in python_indicators:
            if (self.project_root / indicator).exists():
                confidence += 0.3
        
        # Check for Python files
        python_files = list(self.project_root.glob("*.py"))
        if python_files:
            confidence += 0.2
        
        return ("python", confidence)
    
    def _detect_react(self) -> Tuple[str, float]:
        """Detect React project."""
        confidence = 0.0
        
        package_json = self.project_root / "package.json"
        if package_json.exists():
            try:
                import json
                with open(package_json) as f:
                    data = json.load(f)
                
                dependencies = {**data.get('dependencies', {}), **data.get('devDependencies', {})}
                
                if 'react' in dependencies:
                    confidence += 0.6
                if 'react-dom' in dependencies:
                    confidence += 0.2
                if 'react-scripts' in dependencies:
                    confidence += 0.2
                    
            except Exception as e:
                logger.debug(f"Failed to parse package.json: {e}")
        
        return ("react", confidence)
    
    def _detect_vue(self) -> Tuple[str, float]:
        """Detect Vue.js project."""
        confidence = 0.0
        
        package_json = self.project_root / "package.json"
        if package_json.exists():
            try:
                import json
                with open(package_json) as f:
                    data = json.load(f)
                
                dependencies = {**data.get('dependencies', {}), **data.get('devDependencies', {})}
                
                if 'vue' in dependencies:
                    confidence += 0.6
                if '@vue/cli-service' in dependencies:
                    confidence += 0.2
                if 'nuxt' in dependencies:
                    confidence += 0.2
                    
            except Exception as e:
                logger.debug(f"Failed to parse package.json: {e}")
        
        return ("vue", confidence)
    
    def _detect_angular(self) -> Tuple[str, float]:
        """Detect Angular project."""
        confidence = 0.0
        
        if (self.project_root / "angular.json").exists():
            confidence += 0.8
        
        package_json = self.project_root / "package.json"
        if package_json.exists():
            try:
                import json
                with open(package_json) as f:
                    data = json.load(f)
                
                dependencies = {**data.get('dependencies', {}), **data.get('devDependencies', {})}
                
                if '@angular/core' in dependencies:
                    confidence += 0.6
                if '@angular/cli' in dependencies:
                    confidence += 0.2
                    
            except Exception as e:
                logger.debug(f"Failed to parse package.json: {e}")
        
        return ("angular", confidence)
    
    def _detect_go(self) -> Tuple[str, float]:
        """Detect Go project."""
        confidence = 0.0
        
        if (self.project_root / "go.mod").exists():
            confidence += 0.6
        
        if (self.project_root / "go.sum").exists():
            confidence += 0.2
        
        # Check for Go files
        go_files = list(self.project_root.glob("*.go"))
        if go_files:
            confidence += 0.2
        
        return ("go", confidence)
    
    def _detect_rust(self) -> Tuple[str, float]:
        """Detect Rust project."""
        confidence = 0.0
        
        if (self.project_root / "Cargo.toml").exists():
            confidence += 0.8
        
        if (self.project_root / "Cargo.lock").exists():
            confidence += 0.2
        
        return ("rust", confidence)
    
    def _detect_dotnet(self) -> Tuple[str, float]:
        """Detect .NET project."""
        confidence = 0.0
        
        dotnet_files = list(self.project_root.glob("*.csproj")) + \
                      list(self.project_root.glob("*.sln")) + \
                      list(self.project_root.glob("*.fsproj")) + \
                      list(self.project_root.glob("*.vbproj"))
        
        if dotnet_files:
            confidence += 0.8
        
        return ("dotnet", confidence)
    
    def get_project_info(self) -> Dict[str, any]:
        """Get comprehensive project information."""
        project_type, confidence = self.detect_project_type()
        
        return {
            "detected_type": project_type,
            "confidence": confidence,
            "project_root": str(self.project_root),
            "files_found": self._get_relevant_files()
        }
    
    def _get_relevant_files(self) -> List[str]:
        """Get list of relevant project files."""
        relevant_patterns = [
            "pom.xml", "build.gradle", "build.gradle.kts",
            "package.json", "requirements.txt", "setup.py",
            "go.mod", "Cargo.toml", "*.csproj", "*.sln",
            "angular.json", "vue.config.js", "next.config.js"
        ]
        
        found_files = []
        for pattern in relevant_patterns:
            if '*' in pattern:
                found_files.extend([str(f.relative_to(self.project_root)) 
                                  for f in self.project_root.glob(pattern)])
            else:
                file_path = self.project_root / pattern
                if file_path.exists():
                    found_files.append(pattern)
        
        return found_files