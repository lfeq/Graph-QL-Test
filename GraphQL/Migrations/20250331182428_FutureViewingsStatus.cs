using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace ConferencePlanner.GraphQL.Migrations
{
    /// <inheritdoc />
    public partial class FutureViewingsStatus : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.AddColumn<int>(
                name: "Status",
                table: "FutureViewings",
                type: "integer",
                nullable: false,
                defaultValue: 0);
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropColumn(
                name: "Status",
                table: "FutureViewings");
        }
    }
}
