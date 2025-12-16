def build_full_report_email(farm_name, livestock, crops, financial, inventory):
    return f"""
    <h2>{farm_name} – Scheduled Farm Report</h2>

    <p>Hello,</p>
    <p>Your scheduled report is ready. Four PDF reports are attached:</p>

    <ul>
      <li><b>Livestock Report</b></li>
      <li><b>Crops Report</b></li>
      <li><b>Financial Report</b></li>
      <li><b>Inventory Report</b></li>
    </ul>

    <h3>Quick Summary</h3>

    <p><b>Total Livestock:</b> {livestock.get("total_count")}</p>
    <p><b>Total Crop Area:</b> {crops.get("total_area")} hectares</p>
    <p><b>Net Profit:</b> {financial.get("net_profit")}</p>
    <p><b>Total Inventory Items:</b> {inventory.get("total_items")}</p>

    <p>Open the attached PDF files for full details.</p>
    <br/>
    <p>Regards,<br/>FarmXpat System</p>
    """
