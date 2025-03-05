"""
Handles writing formatted resumes.
"""

import logging
import os
import shutil
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_TAB_ALIGNMENT, WD_PARAGRAPH_ALIGNMENT
from docx.enum.style import WD_STYLE_TYPE
from resume.formatter import DocumentFormatter
from resume.parser import ResumeParser


class ResumeWriter:
    """Handles writing formatted resumes"""

    def __init__(self, formatter=None):
        self.formatter = formatter or DocumentFormatter()
        self.parser = ResumeParser()

    def document_writer(self, resume_text, output_path, resume_path):
        try:
            doc = Document()
            self._set_margins(doc)
            self._add_compact_style(doc)

            lines = resume_text.strip().splitlines()

            # Header (Name and Contact)
            name = self._extract_field(lines, "<NAME>")
            contact = self._extract_field(lines, "<CONTACT>")
            self._add_header(doc, name, contact)

            # Executive Summary
            summary = self._extract_field(lines, "<SUMMARY>")
            self.formatter.add_section_heading(doc, "EXECUTIVE SUMMARY")
            self._add_simple_paragraph(doc, summary)

            # Skills
            skills = self._extract_skills(lines)
            doc.add_paragraph("", style="Compact")  # spacing
            self.formatter.add_section_heading(doc, "FUNCTIONAL EXPERTISE")
            self._add_skills_section(doc, skills)

            # Experience
            company_positions = self._extract_experience(lines)
            self._add_experience_section(doc, company_positions)

            # Education
            education_lines = self._extract_section_lines(lines, "<EDUCATION>")
            if education_lines:
                doc.add_paragraph("", style="Compact")
                self.formatter.add_section_heading(doc, "EDUCATION")
                self._add_education_section(doc, education_lines)

            # Volunteerism
            vol_lines = self._extract_section_lines(lines, "<VOLUNTEERISM>")
            if vol_lines:
                doc.add_paragraph("", style="Compact")
                self.formatter.add_section_heading(doc, "VOLUNTEERISM")
                self._add_volunteerism_section(doc, vol_lines)

            # Other Relevant Information
            other_info = self._extract_section_lines(lines, "<OTHER RELEVANT INFORMATION>")
            if other_info:
                doc.add_paragraph("", style="Compact")
                self.formatter.add_section_heading(doc, "OTHER RELEVANT INFORMATION")
                self._add_other_info_section(doc, other_info)

            doc.save(output_path)
            return True

        except Exception as e:
            logging.error(f"Resume rewriting failed: {e}. Falling back to original resume.")
            if os.path.exists(resume_path):
                shutil.copy(resume_path, output_path)
            return False

    # --- Helper methods ---

    def _set_margins(self, doc):
        for section in doc.sections:
            section.top_margin = Inches(0.3)
            section.bottom_margin = Inches(0.3)
            section.left_margin = Inches(0.5)
            section.right_margin = Inches(0.5)

    def _add_compact_style(self, doc):
        styles = doc.styles
        compact = styles.add_style("Compact", WD_STYLE_TYPE.PARAGRAPH)
        compact.base_style = styles["Normal"]
        p_format = compact.paragraph_format
        p_format.space_before = Pt(0)
        p_format.space_after = Pt(3)
        p_format.line_spacing = 1.0
        p_format.alignment = WD_PARAGRAPH_ALIGNMENT.JUSTIFY

    def _extract_field(self, lines, marker):
        for i, line in enumerate(lines):
            if line.strip() == marker and i + 1 < len(lines):
                return lines[i + 1].strip()
        return ""

    def _add_header(self, doc, name, contact):
        header_para = doc.add_paragraph(style="Compact")
        name_run = header_para.add_run(name)
        name_run.bold = True
        name_run.font.size = Pt(16)
        name_run.font.name = "Calibri"

        contact_para = doc.add_paragraph(style="Compact")
        contact_run = contact_para.add_run(contact)
        contact_run.font.size = Pt(11)
        contact_run.font.name = "Calibri"

        # Add spacing after header
        spacing_para = doc.add_paragraph(style="Compact")
        spacing_para.paragraph_format.space_after = Pt(2)

    def _add_simple_paragraph(self, doc, text):
        para = doc.add_paragraph(text, style="Compact")
        run = para.runs[0]
        run.font.size = Pt(11)
        run.font.name = "Calibri"

    def _extract_skills(self, lines):
        skills = []
        in_skills = False
        for line in lines:
            clean_line = line.strip()
            if clean_line == "<SKILLS>":
                in_skills = True
                continue
            if in_skills:
                if clean_line and not line.startswith("<"):
                    if "|" in line:
                        skills.extend(s.strip() for s in line.split("|"))
                    else:
                        skills.append(clean_line)
                elif line.startswith("<"):
                    break
        return skills

    def _add_skills_section(self, doc, skills):
        if not skills:
            return
        skills_per_column = (len(skills) + 1) // 2
        tab_stop = Inches(3.5)
        for i in range(skills_per_column):
            para = doc.add_paragraph(style="Compact")
            para.paragraph_format.tab_stops.add_tab_stop(tab_stop, WD_TAB_ALIGNMENT.LEFT)

            # First column skill
            run = para.add_run("• ")
            run.font.size = Pt(11)
            run.font.name = "Calibri"
            run = para.add_run(skills[i])
            run.font.size = Pt(11)
            run.font.name = "Calibri"

            # Second column skill if available
            if i + skills_per_column < len(skills):
                para.add_run("\t")
                run = para.add_run("• ")
                run.font.size = Pt(11)
                run.font.name = "Calibri"
                run = para.add_run(skills[i + skills_per_column])
                run.font.size = Pt(11)
                run.font.name = "Calibri"

    def _extract_experience(self, lines):
        company_positions = {}
        current_company = None
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if line == "<COMPANY>" and i + 1 < len(lines):
                current_company = lines[i + 1].strip()
                company_positions.setdefault(current_company, [])
                i += 2
                continue

            if line == "<POSITION_DATE>" and current_company and i + 1 < len(lines):
                pos_date = lines[i + 1].strip()
                if "|" in pos_date:
                    position, date = (p.strip() for p in pos_date.split("|", 1))
                    bullets = []
                    i += 2
                    while i < len(lines):
                        current_line = lines[i].strip()
                        if current_line == "<BULLET>" and i + 1 < len(lines):
                            bullets.append(lines[i + 1].strip())
                            i += 2
                        elif current_line in {"<COMPANY>", "<POSITION_DATE>", "<EDUCATION>", "<VOLUNTEERISM>"}:
                            break
                        else:
                            i += 1
                    company_positions[current_company].append((position, date, bullets))
                    continue
            i += 1
        return company_positions

    def _add_experience_section(self, doc, company_positions):
        tab_position = Inches(8.0)  # Adjust for desired date alignment
        for company, positions in company_positions.items():
            company_para = doc.add_paragraph(style="Compact")
            if "|" in company:
                comp_name, location = (s.strip() for s in company.split("|", 1))
                company_text = f"{comp_name} | {location}"
            else:
                company_text = company

            run = company_para.add_run(company_text)
            run.bold = True
            run.font.size = Pt(12)
            run.font.name = "Calibri"
            company_para.paragraph_format.tab_stops.add_tab_stop(tab_position, WD_TAB_ALIGNMENT.RIGHT)

            if len(positions) > 1:
                logging.info(f"Processing multiple positions for company: {company}")
                positions.sort(key=lambda x: self.parser.parse_date(x[1].split("–")[0].strip()),
                            reverse=True)
                all_start = []
                all_end = []
                for _, date_range, _ in positions:
                    if "–" in date_range:
                        parts = date_range.split("–")
                        if len(parts) == 2:
                            start_date = parts[0].strip()
                            end_date = parts[1].strip()
                            all_start.append((start_date, self.parser.parse_date(start_date)))
                            all_end.append((end_date, self.parser.parse_date(end_date)))
                        else:
                            logging.warning(f"Invalid date format: {date_range}")
                    else:
                        logging.warning(f"No date separator found in: {date_range}")

                if all_start and all_end:
                    earliest = sorted(all_start, key=lambda x: x[1])[0][0]
                    latest = sorted(all_end, key=lambda x: x[1], reverse=True)[0][0]
                    date_range_text = f"{earliest} – {latest}"
                else:
                    # Fallback if parsing fails
                    earliest = positions[-1][1].split("–")[0].strip()
                    latest = positions[0][1].split("–")[1].strip()
                    date_range_text = f"{earliest} – {latest}"
                date_run = company_para.add_run("\t" + date_range_text)
                date_run.bold = True
                date_run.font.size = Pt(11)
                date_run.font.name = "Calibri"
            else:
                date_run = company_para.add_run("\t" + positions[0][1])
                date_run.bold = True
                date_run.font.size = Pt(11)
                date_run.font.name = "Calibri"

            for position, date, bullets in positions:
                pos_para = doc.add_paragraph(style="Compact")
                pos_run = pos_para.add_run(position)
                pos_run.italic = True
                pos_run.font.size = Pt(11)
                pos_run.font.name = "Calibri"
                if len(positions) > 1:
                    pos_para.paragraph_format.tab_stops.add_tab_stop(tab_position, WD_TAB_ALIGNMENT.RIGHT)
                    date_run = pos_para.add_run("\t" + date)
                    date_run.italic = True
                    date_run.font.size = Pt(11)
                    date_run.font.name = "Calibri"
                for bullet in bullets:
                    self.formatter.add_bullet_point(doc, bullet)

    def _extract_section_lines(self, lines, marker):
        section_lines = []
        in_section = False
        for line in lines:
            clean = line.strip()
            if clean == marker:
                in_section = True
                continue
            if in_section:
                if clean and not line.startswith("<"):
                    section_lines.append(clean)
                elif line.startswith("<") and clean != marker:
                    break
        return section_lines

    def _add_education_section(self, doc, edu_lines):
        tab_position = Inches(8.0)  # Adjust for desired date alignment
        for i in range(0, len(edu_lines), 3):
            if i + 2 < len(edu_lines):
                para = doc.add_paragraph(style="Compact")
                run = para.add_run("• ")
                run.font.size = Pt(11)
                run.font.name = "Calibri"

                inst_text = edu_lines[i] + "  "
                run = para.add_run(inst_text)
                run.bold = True
                run.font.size = Pt(11)
                run.font.name = "Calibri"

                if "|" in edu_lines[i + 2]:
                    date = edu_lines[i + 2].split("|")[1].strip()
                    para.paragraph_format.tab_stops.add_tab_stop(tab_position, WD_TAB_ALIGNMENT.RIGHT)
                    date_run = para.add_run("\t" + date)
                    date_run.bold = True
                    date_run.font.size = Pt(11)
                    date_run.font.name = "Calibri"

                degree_para = doc.add_paragraph(style="Compact")
                degree_para.paragraph_format.left_indent = Inches(0.25)
                run = degree_para.add_run(edu_lines[i + 1])
                run.font.size = Pt(11)
                run.font.name = "Calibri"

                if "GPA" in edu_lines[i + 2]:
                    gpa = edu_lines[i + 2].split("|")[0].strip() if "|" in edu_lines[i + 2] else edu_lines[i + 2]
                    gpa_para = doc.add_paragraph(style="Compact")
                    gpa_para.paragraph_format.left_indent = Inches(0.25)
                    run = gpa_para.add_run(gpa)
                    run.font.size = Pt(11)
                    run.font.name = "Calibri"

    def _add_volunteerism_section(self, doc, vol_lines):
        tab_position = Inches(8.0)
        for i in range(0, len(vol_lines), 2):
            if i + 1 < len(vol_lines):
                para = doc.add_paragraph(style="Compact")
                run = para.add_run("• ")
                run.font.size = Pt(11)
                run.font.name = "Calibri"
                if "|" in vol_lines[i]:
                    org, date = (s.strip() for s in vol_lines[i].split("|", 1))
                    run = para.add_run(org + "  ")
                    run.bold = True
                    run.font.size = Pt(11)
                    run.font.name = "Calibri"
                    para.paragraph_format.tab_stops.add_tab_stop(tab_position, WD_TAB_ALIGNMENT.RIGHT)
                    date_run = para.add_run("\t" + date)
                    date_run.bold = True
                    date_run.font.size = Pt(11)
                    date_run.font.name = "Calibri"
                else:
                    run = para.add_run(vol_lines[i])
                    run.bold = True
                    run.font.size = Pt(11)
                    run.font.name = "Calibri"

                desc_para = doc.add_paragraph(style="Compact")
                desc_para.paragraph_format.left_indent = Inches(0.25)
                run = desc_para.add_run(vol_lines[i + 1])
                run.font.size = Pt(11)
                run.font.name = "Calibri"

    def _add_other_info_section(self, doc, info_lines):
        """
        Add the 'Other Relevant Information' section with main categories as bullet points
        and include the content right after them.
        
        Args:
            doc: The document object to add the section to.
            info_lines: List of lines containing the other relevant information.
        """
        for line in info_lines:
            para = doc.add_paragraph(style="Compact")
            para.paragraph_format.left_indent = Inches(0.25)
            run = para.add_run("• ")
            run.font.size = Pt(11)
            run.font.name = "Calibri"
            
            if ":" in line:
                category, details = line.split(":", 1)
                run = para.add_run(f"{category.strip()}: ")
                run.bold = True
                run.font.size = Pt(11)
                run.font.name = "Calibri"
                
                # Add details right after the category
                details_run = para.add_run(details.strip())
                details_run.font.size = Pt(11)
                details_run.font.name = "Calibri"
            else:
                run = para.add_run(line.strip())
                run.font.size = Pt(11)
                run.font.name = "Calibri"