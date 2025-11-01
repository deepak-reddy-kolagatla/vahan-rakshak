"""
Gatekeeper Agent - Depot Compliance and Pre-Departure Safety Checks
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from src.tools import (
    CargoScanner, RegulatorAPI
)
from src.models import (
    ComplianceReport, ComplianceStatus, ViolationType, CargoManifest
)

logger = logging.getLogger(__name__)


class GatekeeperAgent:
    """
    Gatekeeper Agent - Digital Inspector at Fleet Depot
    
    Responsibilities:
    - Scan and validate cargo manifests
    - Check compliance with transport regulations
    - Detect prohibited/undeclared materials
    - Lock ignition for non-compliant vehicles
    - Generate compliance reports for regulators
    """

    def __init__(self, agent_id: str = "gatekeeper_v1"):
        """
        Initialize Gatekeeper Agent
        
        Args:
            agent_id: Unique agent identifier
        """
        self.agent_id = agent_id
        self.cargo_scanner = CargoScanner()
        self.regulator_api = RegulatorAPI()
        self.active = False
        self.processed_manifests = []
        self.compliance_reports = []
        
        logger.info(f"Gatekeeper Agent initialized: {agent_id}")

    def start(self) -> None:
        """Start Gatekeeper Agent"""
        self.active = True
        logger.info(f"Gatekeeper Agent {self.agent_id} started")

    def stop(self) -> None:
        """Stop Gatekeeper Agent"""
        self.active = False
        logger.info(f"Gatekeeper Agent {self.agent_id} stopped")

    def process_departure(
        self,
        vehicle_id: str,
        vehicle_number: str,
        vehicle_class: str,
        driver_name: str,
        scanned_by: str
    ) -> Dict[str, Any]:
        """
        Process vehicle departure - main entry point
        
        Args:
            vehicle_id: Vehicle identifier
            vehicle_number: License plate
            vehicle_class: Class of vehicle
            driver_name: Driver name
            scanned_by: Operator scanning cargo
            
        Returns:
            Pre-departure approval decision
        """
        if not self.active:
            logger.warning("Gatekeeper Agent not active")
            return {"status": "error", "message": "Agent not active"}
        
        logger.info(f"Processing departure: {vehicle_number}")
        
        # Step 1: Get scanned cargo manifest
        manifest = self.cargo_scanner.current_manifest
        if not manifest:
            logger.error("No cargo manifest scanned")
            return {
                "status": "failed",
                "message": "No cargo manifest found",
                "approval": False
            }

        # Step 2: Verify cargo compliance
        cargo_types = [item.cargo_type for item in manifest.items]
        cargo_compliance = self.regulator_api.check_cargo_compliance(
            vehicle_class, cargo_types
        )

        # Step 3: Verify weight compliance
        weight_compliance = self.regulator_api.check_weight_compliance(
            vehicle_class, manifest.total_weight_kg
        )

        # Step 4: Create compliance report
        report = self._create_compliance_report(
            vehicle_id=vehicle_id,
            vehicle_number=vehicle_number,
            manifest=manifest,
            cargo_compliance=cargo_compliance,
            weight_compliance=weight_compliance
        )

        # Step 5: Make approval decision
        approval_decision = self._make_approval_decision(report)

        # Step 6: Log and store results
        self.compliance_reports.append(report)
        self.processed_manifests.append(manifest)

        logger.info(
            f"Departure processing complete: {vehicle_number} - "
            f"Approved: {approval_decision['approved']}"
        )

        return approval_decision

    def scan_cargo_qr(self, qr_data: str) -> Dict[str, Any]:
        """
        Scan cargo item QR code
        
        Args:
            qr_data: QR code data
            
        Returns:
            Scanned item details
        """
        return self.cargo_scanner.scan_qr_code(qr_data)

    def scan_cargo_image(self, image_path: str) -> Dict[str, Any]:
        """
        Scan cargo bay image for undeclared items
        
        Args:
            image_path: Path to image file
            
        Returns:
            Image analysis results
        """
        return self.cargo_scanner.scan_cargo_image(image_path)

    def create_manifest(
        self,
        manifest_id: str,
        vehicle_id: str,
        vehicle_number: str,
        driver_name: str,
        scanned_by: str
    ) -> CargoManifest:
        """
        Create cargo manifest from scanned items
        
        Args:
            manifest_id: Manifest identifier
            vehicle_id: Vehicle identifier
            vehicle_number: License plate
            driver_name: Driver name
            scanned_by: Operator name
            
        Returns:
            Created manifest
        """
        return self.cargo_scanner.create_manifest(
            manifest_id, vehicle_id, vehicle_number, driver_name, scanned_by
        )

    def _create_compliance_report(
        self,
        vehicle_id: str,
        vehicle_number: str,
        manifest: CargoManifest,
        cargo_compliance: Dict,
        weight_compliance: Dict
    ) -> ComplianceReport:
        """Create compliance report from checks"""
        report = ComplianceReport(
            report_id=f"RPT_{vehicle_id}_{int(datetime.now().timestamp())}",
            manifest_id=manifest.manifest_id,
            vehicle_id=vehicle_id,
            vehicle_number=vehicle_number,
            status=ComplianceStatus.APPROVED,
            gatekeeper_agent_id=self.agent_id
        )

        # Add violations if found
        if not cargo_compliance.get("compliant", True):
            for violation in cargo_compliance.get("violations", []):
                report.add_violation(
                    ViolationType.PROHIBITED_HAZMAT,
                    violation.get("detail", "")
                )
            report.status = ComplianceStatus.VIOLATION

        if not weight_compliance.get("compliant", True):
            report.add_violation(
                ViolationType.OVERWEIGHT,
                f"Weight: {weight_compliance.get('weight_kg')}kg "
                f"exceeds limit: {weight_compliance.get('limit_kg')}kg"
            )
            report.status = ComplianceStatus.VIOLATION

        return report

    def _make_approval_decision(self, report: ComplianceReport) -> Dict[str, Any]:
        """
        Make approval decision based on compliance report
        
        Args:
            report: Compliance report
            
        Returns:
            Approval decision
        """
        approved = report.status == ComplianceStatus.APPROVED
        
        decision = {
            "approved": approved,
            "report_id": report.report_id,
            "vehicle_locked": not approved,
            "timestamp": report.check_timestamp.isoformat(),
            "violations": report.violations
        }

        if not approved:
            decision["message"] = "DEPARTURE BLOCKED - Compliance violations detected"
            decision["details"] = report.violation_details
            logger.warning(f"Vehicle {report.vehicle_number} departure BLOCKED")
        else:
            decision["message"] = "Departure approved - All compliance checks passed"
            logger.info(f"Vehicle {report.vehicle_number} departure APPROVED")

        return decision

    def get_compliance_history(self, vehicle_id: str) -> List[ComplianceReport]:
        """Get compliance history for vehicle"""
        return [r for r in self.compliance_reports if r.vehicle_id == vehicle_id]

    def submit_report_to_rto(self, report_id: str) -> Dict[str, Any]:
        """
        Submit compliance report to RTO (Regional Transport Office)
        
        Args:
            report_id: Report identifier
            
        Returns:
            Submission status
        """
        report = next(
            (r for r in self.compliance_reports if r.report_id == report_id),
            None
        )
        
        if not report:
            return {"status": "error", "message": "Report not found"}

        # In production, this would send to RTO API
        report.submitted_to_rto = True
        report.rto_submission_timestamp = datetime.now()
        
        logger.info(f"Report {report_id} submitted to RTO")
        
        return {
            "status": "success",
            "report_id": report_id,
            "submitted_at": report.rto_submission_timestamp.isoformat()
        }

    def get_agent_status(self) -> Dict[str, Any]:
        """Get current agent status"""
        return {
            "agent_id": self.agent_id,
            "active": self.active,
            "manifests_processed": len(self.processed_manifests),
            "reports_generated": len(self.compliance_reports),
            "pending_submissions": sum(
                1 for r in self.compliance_reports if not r.submitted_to_rto
            )
        }
