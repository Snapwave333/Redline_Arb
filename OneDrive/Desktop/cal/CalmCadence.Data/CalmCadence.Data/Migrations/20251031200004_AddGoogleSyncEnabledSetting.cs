using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace CalmCadence.Data.CalmCadence.Data.Migrations
{
    /// <inheritdoc />
    public partial class AddGoogleSyncEnabledSetting : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.AddColumn<bool>(
                name: "GoogleSyncEnabled",
                table: "Settings",
                type: "INTEGER",
                nullable: false,
                defaultValue: false);

            migrationBuilder.UpdateData(
                table: "Settings",
                keyColumn: "Id",
                keyValue: 1,
                column: "GoogleSyncEnabled",
                value: false);
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropColumn(
                name: "GoogleSyncEnabled",
                table: "Settings");
        }
    }
}
